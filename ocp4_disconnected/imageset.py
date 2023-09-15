#!/usr/bin/env python3

from pathlib import Path

import colorlog
import yaml

from . import BASE_DIR


colorlog.basicConfig(
    format='%(log_color)s%(levelname)s%(reset)s:%(asctime)s:%(name)s:%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=colorlog.WARNING,
)
logger = colorlog.getLogger('imageset')
logger.setLevel(colorlog.DEBUG)


# https://github.com/openshift/oc-mirror/blob/main/docs/imageset-config-ref.yaml
class ImagesetConfig():
    def __init__(self, openshift_version_xyz: str, config_dir: Path, storage_dir: Path) -> None:
        self.openshift_version_xyz = openshift_version_xyz
        self.config_dir = config_dir
        self.storage_dir = storage_dir

        self.config_path = self.config_dir.joinpath(f'imageset-config.yaml')

        self.openshift_version_xy = '.'.join(self.openshift_version_xyz.split('.')[0:2])
        self.openshift_release_channel = f'fast-{self.openshift_version_xy}'
        self.imageset_config = self._imageset_config()

    def _imageset_config(self) -> dict:
        if self.config_path.is_file():
            with self.config_path.open('r') as f:
                return yaml.safe_load(f)

        with BASE_DIR.joinpath('imageset-config-template.yaml').open('r') as f:
            return yaml.safe_load(f)

    def set_storage_config(self) -> None:
        self.imageset_config['storageConfig']['local']['path'] = str(self.storage_dir.absolute())

    def append_openshift_release(self) -> None:
        channels = self.imageset_config['mirror']['platform']['channels']
        for channel in channels:
            if channel['name'] == self.openshift_release_channel:
                logger.info(f'Found release channel in imageset config, updating version range')

                min_version_z_stream = int(channel['minVersion'].split('.')[2])
                max_version_z_stream = int(channel['maxVersion'].split('.')[2])
                z_stream = int(self.openshift_version_xyz.split('.')[2])

                if z_stream < min_version_z_stream:
                    logger.info(f'OpenShift version {self.openshift_version_xyz} is less than current minimum version in imageset, updating')
                    channel['minVersion'] = self.openshift_version_xyz
                elif z_stream > max_version_z_stream:
                    logger.info(f'OpenShift version {self.openshift_version_xyz} is greater than current maximum version in imageset, updating')
                    channel['maxVersion'] = self.openshift_version_xyz
                return

        self.imageset_config['mirror']['platform']['channels'].append({
            'name': self.openshift_release_channel,
            'type': 'ocp',
            'minVersion': self.openshift_version_xyz,
            'maxVersion': self.openshift_version_xyz,
            'shortestPath': True,
        })

    def append_operator_catalog(self) -> None:
        pass

    def append_additional_images(self) -> None:
        pass

    def create_imageset_config(self) -> None:
        self.set_storage_config()
        self.append_openshift_release()
        self.append_operator_catalog()
        self.append_additional_images()

        logger.info(f'Writing imageset config to {self.config_path}')
        with self.config_path.open('w') as f:
            yaml.dump(self.imageset_config, f)
