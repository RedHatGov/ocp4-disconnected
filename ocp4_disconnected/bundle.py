#!/usr/bin/env python3

import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile

import click
import colorlog
import requests
from requests.compat import urljoin
from tqdm import tqdm

from . import MIRROR_URL
from .imageset import ImagesetConfig


CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help'],
    max_content_width=100,
)

colorlog.basicConfig(
    format='%(log_color)s%(levelname)s%(reset)s:%(asctime)s:%(name)s:%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=colorlog.WARNING,
)
logger = colorlog.getLogger('bundle')
logger.setLevel(colorlog.DEBUG)


class Bundle():
    def __init__(self, openshift_version: str, output_dir: str, pull_secret: str) -> None:
        self.openshift_version = openshift_version
        self.output_dir = Path(output_dir)
        self.pull_secret = pull_secret

        self.real_openshift_version = self._real_openshift_version()
        self.repos_dir = self.output_dir.joinpath('repos')
        self.images_dir = self.output_dir.joinpath('images')
        self.metadata_dir = self.output_dir.joinpath('metadata')
        self.binaries_dir = self.output_dir.joinpath('bin')

        self.clients_dir = self.output_dir.joinpath('clients')
        self.clients_version_dir = self.clients_dir.joinpath(self.real_openshift_version)

        self.docker_config_dir = Path.home().joinpath('.docker')
        self.make_output_dirs()

    def _release_info(self) -> str:
        version_url = self.openshift_version

        match = re.fullmatch(r'(4\.\d+)', self.openshift_version)
        if match:
            version_url = f'stable-{self.openshift_version}'
            logger.info(f'Converted {self.openshift_version} to {version_url} for release info URL')

        try:
            r = requests.get(urljoin(MIRROR_URL, f'ocp/{version_url}/release.txt'))
            r.raise_for_status()
        except requests.HTTPError:
            logger.exception(f'Unable to find release info for OpenShift version {self.openshift_version}')
            raise

        return r.text

    def _real_openshift_version(self) -> str:
        release_info = self._release_info()

        match = re.search(r'Name:\s+(4\.\d+\.\d+)', release_info)
        if match:
            logger.info(f'Using OpenShift version {match.group(1)}')
            real_version = match.group(1)
        else:
            raise ValueError('Unable to find OpenShift version number in release info')

        if int(real_version.split('.')[1]) < 10:
            raise ValueError('OpenShift versions before 4.10 are not supported by this tool')

        return real_version

    def make_output_dirs(self) -> None:
        output_dirs = [
            self.repos_dir,
            self.images_dir,
            self.metadata_dir,
            self.binaries_dir,
            self.clients_dir,
            self.clients_version_dir,
            self.docker_config_dir,
        ]
        for directory in output_dirs:
            directory.mkdir(parents=True, exist_ok=True)

    def download_with_progress_bar(self, url: str, output_path: Path) -> Path:
        try:
            r = requests.get(url, stream=True)
            r.raise_for_status()
        except requests.HTTPError:
            logger.exception(f'Unable to download {url}')

        progress_bar = tqdm(total=int(r.headers.get('content-length', 0)), unit='iB', unit_scale=True)
        with output_path.open('wb') as f:
            for data in r.iter_content(1024):
                progress_bar.update(len(data))
                f.write(data)
        progress_bar.close()

        return output_path

    def download_cli_artifacts(self, name: str, filename: str, output_dir: Path = None, url: str = None) -> Path:
        if output_dir is None:
            output_dir = self.clients_version_dir

        output_path = output_dir.joinpath(filename)

        if not output_path.is_file():
            logger.info(f'Downloading the {name}')

            if not url:
                url = urljoin(MIRROR_URL, f'ocp/{self.real_openshift_version}/{filename}')
            output_path = self.download_with_progress_bar(url, output_path)

            logger.info(f'{name} download complete')
        else:
            logger.info(f'{name} has already been downloaded, skipping')

        return output_path

    def extract_binaries(self, tarfile_path: Path, binaries: list) -> None:
        if binaries:
            logger.info(f'Extracting <{", ".join(binaries)}> from {tarfile_path}')
        else:
            logger.info(f'Extracting {tarfile_path}')

        def extract(tar):
            for name in tar.getnames():
                output_path = self.binaries_dir.joinpath(name)
                if binaries:
                    if name in binaries:
                        if output_path.is_file():
                            logger.info(f'File already extracted {output_path}, skipping')
                        else:
                            tar.extract(name, path=self.binaries_dir)
                        # Ensure the extracted binary is executable
                        output_path.chmod(0o755)
                else:
                    if output_path.is_file():
                        logger.info(f'File already extracted {output_path}, skipping')
                    else:
                        tar.extract(name, path=self.binaries_dir)

        with tarfile.open(str(tarfile_path)) as tar:
            extract(tar)
        logger.info(f'Extracting complete for {tarfile_path}')

    def download_installer(self) -> None:
        self.download_cli_artifacts('OpenShift installer', 'openshift-install-linux.tar.gz')

    def download_clients(self) -> None:
        output_path = self.download_cli_artifacts('OpenShift clients', 'openshift-client-linux.tar.gz')
        self.extract_binaries(output_path, ['oc', 'kubectl'])

    def download_oc_mirror(self) -> None:
        output_path = self.download_cli_artifacts('OpenShift mirror plugin', 'oc-mirror.tar.gz')
        self.extract_binaries(output_path, ['oc-mirror'])

    def download_mirror_registry(self) -> None:
        self.download_cli_artifacts('OpenShift mirror registry', 'mirror-registry.tar.gz', output_dir=self.clients_dir,
                                    url=urljoin(MIRROR_URL, 'mirror-registry/latest/mirror-registry.tar.gz'))

    def mirror_images(self, attempt_count: int = 1) -> None:
        # TODO: see if symlinking to the /mnt/data path works
        # TODO: check if file exists before writing as to not clobber an existing one
        docker_config = self.docker_config_dir.joinpath('config.json')
        logger.info(f'Writing pull secret to {docker_config}')
        docker_config.write_text(self.pull_secret)

        imageset_config = ImagesetConfig(self.real_openshift_version, self.output_dir, self.metadata_dir)
        imageset_config.create_imageset_config()

        cmd_env = {
            'PATH': f'{self.binaries_dir}:$PATH',
            'HOME': str(Path.home()),
        }

        logger.info(f'Mirroring images using config {imageset_config.config_path} (grab a coffee, this will take a while)')
        mirror = subprocess.run(
            [
                'oc',
                'mirror',
                '--config', imageset_config.config_path.absolute(),
                f'file://{self.images_dir.absolute()}',
            ],
            env=cmd_env,
            cwd=self.metadata_dir,
        )

        # I'm not sure why, but the mirror command fails sometimes. Should we retry a few times before giving up?
        # https://github.com/openshift/oc-mirror/issues/175
        try:
            mirror.check_returncode()
        except subprocess.CalledProcessError:
            if attempt_count >= 3:
                raise

            logger.error('This failture seems to happen occasionally, retry again')
            self.mirror_images(attempt_count+1)

    def download_rpms(self) -> None:
        logger.info('Downloading RPMs for podman and its dependencies')

        p = subprocess.run(
            [
                '/usr/bin/repotrack',
                '--disablerepo=*',
                '--enablerepo=ubi-8-appstream-rpms',
                '--enablerepo=ubi-8-baseos-rpms',
                '--destdir',
                self.repos_dir,
                'podman',
            ]
        )

        logger.info('Completed RPM downloads')

    def cleanup(self) -> None:
        shutil.rmtree(self.images_dir.joinpath('oc-mirror-workspace'))

    def bundle(self) -> None:
        self.download_installer()
        self.download_clients()
        self.download_oc_mirror()
        self.download_mirror_registry()
        self.mirror_images()
        self.download_rpms()
        self.cleanup()

        # TODO: Bundle incremental data since last run instead of all data
        bundle_path = self.output_dir.joinpath('ocp4_bundle.tar')
        logger.info(f'Bundling all content into tar file at {bundle_path}')
        with tarfile.open(str(bundle_path), 'w') as tar:
            logger.info('Adding clients to tar file')
            tar.add(self.clients_dir, arcname=self.clients_dir.stem)
            logger.info('Adding images to tar file')
            tar.add(self.images_dir, arcname=self.images_dir.stem)
            logger.info('Adding repos to tar file')
            tar.add(self.repos_dir, arcname=self.repos_dir.stem)

        logger.info('Completed bundle')


def get_pull_secret(ctx, param, value):
    output_path = Path(ctx.params['output_dir']).joinpath('pull-secret.json')

    if output_path.is_file() and value is None:
        return output_path.read_text()

    if value is None:
        pull_secret = click.prompt('Pull Secret (input hidden)', hide_input=True)
        return get_pull_secret(ctx, param, pull_secret)
    else:
        try:
            json.loads(value)
        except json.JSONDecodeError:
            raise click.BadParameter('The pull secret specified is not valid JSON')
        output_path.write_text(value)
        return value

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--openshift-version', prompt='OpenShift Version', required=True, default='latest',
              help='The version of OpenShift (e.g. 4.12, 4.12.23, latest) you would like to create an air-gapped package for')
@click.option('--output-dir', prompt='Output Directory', is_eager=True, required=True,
              help='The directory to output the content needed for an air-gapped install')
@click.option('--pull-secret', required=False, callback=get_pull_secret,
              help='The pull secret used to pull images from Red Hat')
def main(openshift_version, pull_secret, output_dir):
    """Bundle all of the artifacts needed for an OpenShift 4 install in a
    disconnected / air-gapped environment.

    When prompted for your Pull Secret, it can be found at:
    https://console.redhat.com/openshift/install/pull-secret
    """
    b = Bundle(openshift_version, output_dir, pull_secret)
    b.bundle()

main()
