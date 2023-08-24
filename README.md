# OpenShift 4 Disconnected Bundler

A tool to make it easy to get started when deploying OpenShift clusters in a
disconnected / air-gapped network. The tool will bundle up all of the requireed
dependencies (e.g. container images, CLI tools, etc.) that can be transfered to
the disconnected environment. The generated bundle includes a script to unpack
and host the artifacts in the disconnected environment so that they can be used
to install OpenShift.

## Initial Setup

### Build Container

This tool is meant to be run inside of a container and needs to be built. The
`--platform=linux/amd64` option is important to ensure the container works as
expected on Apple silicon Macs.

> [!NOTE]
> Eventually this container will be available to be pulled without building it
> yourself, but while this is under active development, that is not the case.

```bash
podman build --layers --tag ocp4-disconnected --platform=linux/amd64 .
```

### Pull Secret

In order to pull the container images required to install OpenShift, you will
need a pull secret that allows you to authenticate to the Red Hat registry.

If you do not already have a Red Hat account, registr for a [FREE Red Hat
Developer account](https://developers.redhat.com/register/) that will give you
access to Red Hat software, including the ability to get the pull secret needed
for this tool.

You can find your pull secret at
https://console.redhat.com/openshift/install/pull-secret

Keep this page handy as you will be prompted for the value of your pull secret
when you get ready to run the tool.

## Bundle OpenShift Dependencies

### Quick Start

```bash
podman run -it --rm --volume ocp4_data:/mnt/data localhost/ocp4-disconnected
```

### Usage

If you do not pass any parameters, you will be prompted for the required
parameters. To see the available parameters, you can pass `--help` or `-h`.

> [!WARNING]
> It is **NOT** recommended to override `--output-dir` as it is already
> configured as part of the container to output to `/mnt/data`. You should map
> a volume in your `podman run` (as seen above in the quick start) to
> `/mnt/data` to ensure your data persists.

```
Usage: bundle.py [OPTIONS]

  Bundle all of the artifacts needed for an OpenShift 4 install in a disconnected / air-gapped
  environment.

  When prompted for your Pull Secret, it can be found at:
  https://console.redhat.com/openshift/install/pull-secret

Options:
  --openshift-version TEXT  The version of OpenShift (e.g. 4.12, 4.12.23, latest) you would like
                            to create an air-gapped package for  [required]
  --output-dir TEXT         The directory to output the content needed for an air-gapped install
                            [required]
  --pull-secret TEXT        The pull secret used to pull images from Red Hat
  -h, --help                Show this message and exit.
```
