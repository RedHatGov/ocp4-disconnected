# OpenShift 4 Disconnected Bundler Documentation

## Bundle Content

For our walkthrough, we will be using the Jump host as our host to download the
content bundle since it has access to the internet. This isn't required and
these steps could be done from your laptop or any other internet connected
host. We are doing using the jump host in this case because it has a fast
connection to the internet and is avaliable as part of our simulated
disconnected environment in the nxext step.

Start by connecting to the Jump host via SSH. You can grab the public IP of the
Jump host from the outputs captured during the environment prep stage or you
can use the command below as a convenience.

```bash
export JUMP_HOST_PUBLIC_IP=$(aws cloudformation describe-stacks --stack-name ocp4-disconnected --query 'Stacks[0].Outputs[?OutputKey==`JumpInstancePublicIp`].OutputValue' --output text)

ssh-add ~/.ssh/ocp4-disconnected
ssh ec2-user@${JUMP_HOST_PUBLIC_IP}
```

### Pull Secret

In order to pull the container images required to install OpenShift, you will
need a pull secret that allows you to authenticate to the Red Hat registry.

If you do not already have a Red Hat account, register for a [FREE Red Hat
Developer account](https://developers.redhat.com/register/) that will give you
access to Red Hat software, including the ability to get the pull secret needed
for this tool.

You can find your pull secret on the [Red Hat OpenShift
Console](https://console.redhat.com/openshift/install/pull-secret)

Keep this page handy as you will be prompted for the value of your pull secret
when you get ready to run the tool.

### Download and Package Content

We will now run this tool the download and package the content we'll need in
order to perform an install of OpenShift in a disconnected environment in the nxext step This
.tool accepts a few parameters and will prompt for any that are not passed in.
For this walkthrough, we will use the tool in that method and have it prompt us
for the required input.

> [!WARNING]
> If you choose to specify parameters via the CLI instead of being prompted, it
> is **NOT** recommended to override `--output-dir` as it is already
> configured as part of the container to output to `/mnt/data`. You should map
> a volume in your `podman run` (as seen below) to `/mnt/data` to ensure your
> data persists.

The information that we need to give the tool is the OpenShift version to
download content for and our pull secret from above. The pull secret only needs
to be specified on the first run as it will be saved and used for future runs.

If you do not specify the OpenShift version when prompted, it will default to
the latest stable version. You can also specify the version in the format of
`x.y` (e.g. `4.12`) and it will find the latest stable of that version. If you
want a specific z-stream release, you can also specify the version as `x.y.z`
(e.g. `4.12.30`).

```bash
podman pull ghcr.io/jaredhocutt/ocp4-disconnected:latest

podman run -it --rm --name ocp4-disconnected --platform linux/amd64 --volume /mnt/ocp4_data:/mnt/data:z ghcr.io/jaredhocutt/ocp4-disconnected:latest
```

After the tool finishes, all of the content we need is in a single tar file at
`/mnt/ocp4_data/ocp4_bundle.tar`.

If you are doing this in a different environment than this simulated
environment and have passed a different path as your `--volume` mapping in the
command above, the `ocp4_bundle.tar` will be in whichever directory you
specified.

### Transfer Content

Now that we have our `ocp4_bundle.tar`, we are ready to transfer to the
disconnected environment. As mentioned earlier, in a real environment we would
follow the approved process for transferring content to our disconnected
environment, but for this walkthrough we will be using an S3 bucket. You can
grab the name of the S3 bucket from the outputs captured during the environment
prep stage or you can use the command below as a convenience.

```bash
export S3_TRANSFER_BUCKET=$(aws cloudformation describe-stacks --stack-name ocp4-disconnected --query 'Stacks[0].Outputs[?OutputKey==`S3TransferBucket`].OutputValue' --output text)

aws s3 cp /mnt/ocp4_data/ocp4_bundle.tar s3://${S3_TRANSFER_BUCKET}
```

At this point, we are done with the work we need to do in the connected
environment. In the next steps, we will be working in the disconnected
environment.

[<< Back: Prepare Environment](../README.md) - [Next: Unpack Content >>](unpack_content.md)
