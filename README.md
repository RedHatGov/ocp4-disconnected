# OpenShift 4 Air-Gapped Bundler

## Build Container

```bash
podman build --layers --tag openshift4-airgap .
```

## Run Bundler

```bash
podman run -it --rm --volume airgap_data:/mnt/data localhost/openshift4-airgap
```

If you do not pass any parameters, you will be prompted for the required
parameters. To see the available parameters, you can pass `--help` or `-h`.

It is **NOT** recommended to override `--output-dir` as it is already
configured as part of the container to output to `/mnt/data`. You should map a
volume in your `podman run` (as seen above) to `/mnt/data` to ensure your data
persists.

```
Usage: bundle.py [OPTIONS]

Options:
  --openshift-version TEXT  The version of OpenShift (e.g. 4.12, 4.12.23,
                            latest) you would like to create an air-gapped
                            package for
  --output-dir TEXT         The directory to output the content needed for an
                            air-gapped install
  -h, --help                Show this message and exit.
```
