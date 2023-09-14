# OpenShift 4 Disconnected Bundler

A tool that makes it easier to get started when deploying OpenShift clusters in
a disconnected / air-gapped networks. The tool will bundle up all of the
required dependencies (e.g. container images, CLI tools, etc.) that can be
transfered to the disconnected environment. The generated bundle includes a
script to unpack and host the artifacts in the disconnected environment so that
they can be used to install OpenShift.

For a walkthrough of how to use the tool, including deploying a simulated
disconnected environment, [take a look at the docs](docs/index.md).
