#!/usr/bin/env python3

from pathlib import Path
import re
import subprocess
import tarfile

import click
import colorlog
import requests
from requests.compat import urljoin
from tqdm import tqdm


MIRROR_URL = 'https://mirror.openshift.com/pub/openshift-v4/clients/'
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
    def __init__(self, openshift_version, output_dir) -> None:
        self.openshift_version = openshift_version
        self.output_dir = output_dir

        self.real_openshift_version = self._real_openshift_version()
        self.version_dir = Path(self.output_dir).joinpath(self.real_openshift_version)
        self.download_dir = Path(self.version_dir).joinpath('download')
        self.binaries_dir = Path(self.version_dir).joinpath('bin')
        self.docker_config_dir = Path.home().joinpath('.docker')
        self.make_output_dirs()

        self._pull_secret = None

    @property
    def pull_secret(self) -> str:
        if not self._pull_secret:
            self._pull_secret = Path(self.output_dir).joinpath('pull-secret.json').read_text()

        return self._pull_secret

    def make_output_dirs(self) -> None:
        for directory in [self.version_dir, self.download_dir, self.binaries_dir, self.docker_config_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def download_with_progress_bar(self, url: str, filename: str) -> None:
        try:
            r = requests.get(url, stream=True)
            r.raise_for_status()
        except requests.HTTPError:
            logger.exception(f'Unable to download {url}')

        progress_bar = tqdm(total=int(r.headers.get('content-length', 0)), unit='iB', unit_scale=True)
        with Path(self.download_dir).joinpath(filename).open('wb') as f:
            for data in r.iter_content(1024):
                progress_bar.update(len(data))
                f.write(data)
        progress_bar.close()

    def download_cli_artifacts(self, name: str, filename: str, url: str = None) -> None:
        if not Path(self.download_dir).joinpath(filename).is_file():
            logger.info(f'Downloading the {name}')

            if not url:
                url = urljoin(MIRROR_URL, f'ocp/{self.real_openshift_version}/{filename}')
            self.download_with_progress_bar(url, filename)

            logger.info(f'{name} download complete')
        else:
            logger.info(f'{name} has already been downloaded, skipping')

    def extract_binaries(self, filename: str, binaries: list) -> None:
        if binaries:
            logger.info(f'Extracting <{", ".join(binaries)}> from {filename}')
        else:
            logger.info(f'Extracting {filename}')

        def extract(tar):
            for name in tar.getnames():
                output_path = Path(self.binaries_dir).joinpath(name)
                if binaries:
                    if name in binaries:
                        if output_path.is_file():
                            logger.info(f'File already extracted {output_path}, skipping')
                        else:
                            tar.extract(name, path=self.binaries_dir)
                else:
                    if output_path.is_file():
                        logger.info(f'File already extracted {output_path}, skipping')
                    else:
                        tar.extract(name, path=self.binaries_dir)

        with tarfile.open(str(Path(self.download_dir).joinpath(filename))) as tar:
            extract(tar)
        logger.info(f'Extracting complete for {filename}')

    def download_installer(self) -> None:
        filename = 'openshift-install-linux.tar.gz'
        self.download_cli_artifacts('OpenShift installer', filename)
        self.extract_binaries(filename, ['openshift-install'])

    def download_clients(self) -> None:
        filename = 'openshift-client-linux.tar.gz'
        self.download_cli_artifacts('OpenShift clients', filename)
        self.extract_binaries(filename, ['oc', 'kubectl'])

    def download_oc_mirror(self) -> None:
        filename = 'oc-mirror.tar.gz'
        self.download_cli_artifacts('OpenShift mirror plugin', filename)
        self.extract_binaries(filename, ['oc-mirror'])
        # The oc-mirror binary isn't executable by default, but needs to be
        Path(self.binaries_dir).joinpath('oc-mirror').chmod(0o755)

    def download_mirror_registry(self) -> None:
        filename = 'mirror-registry.tar.gz'
        self.download_cli_artifacts('OpenShift mirror registry', filename,
                                    url=urljoin(MIRROR_URL, 'mirror-registry/latest/mirror-registry.tar.gz'))
        self.extract_binaries(filename, None)

    def mirror_images(self) -> None:
        docker_config = Path(self.docker_config_dir).joinpath('config.json')
        imageset_config = Path(self.version_dir).joinpath('imageset-config.yaml')

        logger.info(f'Writing pull secret to {docker_config}')
        docker_config.write_text(self.pull_secret)

        cmd_env = {
            'PATH': f'{self.binaries_dir}:$PATH',
            'HOME': str(Path.home()),
        }

        logger.info('Generating the image set configuration (this may take a few minutes)')
        mirror_init = subprocess.run(
            [
                'oc',
                'mirror',
                'init'
            ], env=cmd_env, capture_output=True
        )

        logger.info(f'Saving the image set configuration to {imageset_config}')
        imageset_config.write_bytes(mirror_init.stdout)

        logger.info(f'Mirroring images using config {imageset_config} (grab a coffee, this will take a while)')
        mirror = subprocess.run(
            [
                'oc',
                'mirror',
                '--config',
                imageset_config, f'file://{self.version_dir}',
            ], env=cmd_env
        )

    def bundle(self) -> None:
        self.download_installer()
        self.download_clients()
        self.download_oc_mirror()
        self.download_mirror_registry()
        self.mirror_images()
        logger.info('Completed bundle')

    def _release_info(self) -> str:
        version_url = self.openshift_version

        match = re.fullmatch(r'(4\.\d+)', self.openshift_version)
        if match:
            version_url = f'latest-{self.openshift_version}'
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


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--openshift-version', prompt='OpenShift Version',
              required=True, default='latest',
              help='The version of OpenShift (e.g. 4.12, 4.12.23, latest) you would like to create an air-gapped package for')
@click.option('--pull-secret', required=False,
              help='The pull secret used to pull images from Red Hat')
@click.option('--output-dir', prompt='Output Directory', required=True,
              help='The directory to output the content needed for an air-gapped install')
def main(openshift_version, pull_secret, output_dir):
    """Bundle all of the artifacts needed for an OpenShift 4 install in an
    air-gapped cluster.

    When prompted for your Pull Secret, it can be found at:
    https://console.redhat.com/openshift/install/pull-secret
    """
    pull_secret_path = Path(output_dir).joinpath('pull-secret.json')

    pull_secret_value = None
    if pull_secret is not None:
        if pull_secret_path.is_file():
            logger.info(f'Overwriting existing pull secret at {pull_secret_path}')
        pull_secret_value = pull_secret
    elif pull_secret_path.is_file():
        logger.info(f'Found existing pull secret at {pull_secret_path}')
    else:
        pull_secret_value = click.prompt('Pull Secret')

    if pull_secret_value is not None:
        pull_secret_path.write_text(pull_secret_value)
        logger.info(f'Saved pull secret to {pull_secret_path}')

    b = Bundle(openshift_version, output_dir)
    b.bundle()


if __name__ == '__main__':
    main()
