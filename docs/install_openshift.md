# OpenShift 4 Disconnected Bundler Documentation

## Install OpenShift

Now that our disconnected environment is setup and our registry has the
required content, we're ready to install OpenShift.

As mentioned in the previous section, we need to create an
`install-config.yaml` that will tell OpenShift how to perform the installation.
As part of generating this file, we will also be sure to copy and paste the
configuration output of the `unpack.sh` script to the bottom of our generated
file.

### Create Install Configuration

The details of what goes in the `install-config.yaml` will differ depending on
the target platform where your OpenShift cluster will be running. In this
walkthrough, we will be targeting the simulated disconnected environment that
we created in AWS, but for details for other target platforms, you can refer to
the [OpenShift documentation][ocp_platforms].

For the purposes of our walkthrough, we will use the High Side host since it is
already available in the disconnected environment. It's not required to do the
installation from the same host where the content is being hosted and we are
only doing it for convenience in this walkthrough.

If you are not already, connect to the High Side host via SSH.

```bash
export JUMP_HOST_PUBLIC_IP=$(aws cloudformation describe-stacks --stack-name ocp4-disconnected --query 'Stacks[0].Outputs[?OutputKey==`JumpInstancePublicIp`].OutputValue' --output text)
export HIGHSIDE_HOST_PRIVATE_IP=$(aws cloudformation describe-stacks --stack-name ocp4-disconnected --query 'Stacks[0].Outputs[?OutputKey==`HighSideInstancePrivateIp`].OutputValue' --output text)

ssh-add ~/.ssh/ocp4-disconnected
ssh -J ec2-user@${JUMP_HOST_PUBLIC_IP} ec2-user@${HIGHSIDE_HOST_PRIVATE_IP}
```

Create an SSH key to use for the OpenShift cluster.

```bash
ssh-keygen -q -N '' -f ~/.ssh/ocp4-install
```

Create a directory to use as workspace for the installation.

```bash
mkdir ~/ocp4-install
```

Before we run the installer to generate our `install-config.yaml`, we need to
create our pull secret for the disconnected environment that contains the
authentication information for our mirror registry.

```bash
export REGISTRY_USERNAME=openshift
export REGISTRY_PASSWORD=$(echo -n `head -n 1 /mnt/ocp4_data/registry/registry_password`)

cat << EOF | jq -r tostring > ~/pull-secret.json
{
  "auths": {
    "$(hostname --fqdn):8443": {
      "auth": "$(echo -n "openshift:${REGISTRY_PASSWORD}" | base64 -w0)"
    }
  }
}
EOF

cat ~/pull-secret.json
```

You will want to copy the output to your clipboard.

To start, we will use the `openshift-install` command to generate the initial
`install-config.yaml` by answering the prompts.


```bash
openshift-install create install-config --dir ~/ocp4-install
```

The table below shows the descriptions of each prompt you will see.

| Prompt         | Description                                                                                                                                                        |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| SSH Public Key | The SSH public key used to access all nodes within the cluster.                                                                                                    |
| Platform       | The platform on which the cluster will run. For a full list of platforms, including those not supported by this wizard, see https://github.com/openshift/installer |
| Region         | The AWS region to be used for installation.                                                                                                                        |
| Base Domain    | The base domain of the cluster. All DNS records will be sub-domains of this base and will also include the cluster name.                                           |
| Cluster Name   | The name of the cluster. This will be used when generating sub-domains.                                                                                            |
| Pull Secret    | The container registry pull secret for this cluster, as a single line of JSON (e.g. `{"auths": {...}}`).                                                           |

For the purposes of our walkthrough, we'll want to answer the prompts as shown
below.

> [!IMPORTANT]
> If you have a domain you want to pushlish your cluster under, you can set
> **Base Domain** to that instead of `example.com`. The full domain of your
> cluster will become `{{ Cluster Name }}.{{ Base Domain }}`, so be sure to set
> **Base Domain** accordingly.
>
> However, we will be deploying this cluster isolated to the VPC only, so using
> any **Base Domain** will suffice since it will resolve within the VPC via a
> private Route53 zone.

```text
? SSH Public Key /home/ec2-user/.ssh/ocp4-install.pub
? Platform aws
? Region us-east-2
? Base Domain example.com
? Cluster Name ocp4-disconnected
? Pull Secret [? for help] ********************************************************************************************************************************
```

After answering the prompts, our `install-config.yaml` is located at
`~/ocp4-install/install-config.yaml`. Before we are able to start the install,
we need to add some items to the `install-config.yaml` file. Specifically,
since we are deploying into an existing VPC, we need to let the installer know
which subnets to use and the details to pull images from our mirror registry.

To make this easier, we'll take advantage of the AWS CLI and `yq` to make these
edits for us. However, to describe what we're doing, we are updating
`platform.aws.subnets` to be the list of disconnected subnets from our VPC and
also updating `networking.machineNetwork` to contain the CIDR of those subnets.

```bash
export PRIVATE_SUBNETS=$(aws cloudformation describe-stacks --stack-name ocp4-disconnected --query 'Stacks[0].Outputs[?OutputKey==`PrivateSubnets`].OutputValue' --output text | sed 's/,/\n/g')

yq -i '.platform.aws.subnets = []' ~/ocp4-install/install-config.yaml
yq -i '.networking.machineNetwork = []' ~/ocp4-install/install-config.yaml
yq -i '.publish = "Internal"' ~/ocp4-install/install-config.yaml

for subnet in ${PRIVATE_SUBNETS}; do
  yq -i '.platform.aws.subnets += "'${subnet}'"' ~/ocp4-install/install-config.yaml
  yq -i '.networking.machineNetwork += {"cidr": '$(aws ec2 describe-subnets --subnet-ids ${subnet} | jq '.Subnets[0].CidrBlock')'}'  ~/ocp4-install/install-config.yaml
done
```

After we run the commands above, in our `install-config.yaml` we should see the
`platform.aws.subnets` and `networking.machineNetwork` updated to look similar
to the output below.

```yaml
networking:
  clusterNetwork:
    - cidr: 10.128.0.0/14
      hostPrefix: 23
  machineNetwork:
    - cidr: 10.0.48.0/20
    - cidr: 10.0.64.0/20
    - cidr: 10.0.80.0/20
  networkType: OVNKubernetes
  serviceNetwork:
    - 172.30.0.0/16

platform:
  aws:
    region: us-east-2
    subnets:
      - subnet-067e552c71153a6a3
      - subnet-05a8d8fe1fd2accfe
      - subnet-004cc1714240d33db
```

The last modification we need to make to our `install-config.yaml` is to add
the output from the `unpack.sh` script that will tell the OpenShift installer
where to find the images in the mirror registry.

```bash
yq -i '. *= load("/mnt/ocp4_data/registry/install_config_registry.yaml")' ~/ocp4-install/install-config.yaml
```

We're almost ready to start the OpenShift installation. One last thing we'll do
is make a backup copy of our `install-config.yaml` because the installation
process will consume the one in `~/ocp4-install`.

```bash
cp ~/ocp4-install/install-config.yaml ~/ocp4-install/install-config.yaml.bak
```

During the OpenShift installation process, the installer creates all of the AWS
resources required for the OpenShift cluster. We will need an IAM User with the
[appropriate permissions][iam_permissions] to perform this installation, which
was already created for us by the CloudFormation template for our simulated
disconnected environment.

We first need to create keys we can use before we run the OpenShift installer.

```bash
export OCP_INSTALL_ACCESS_KEY=$(aws iam create-access-key --user-name $(aws cloudformation describe-stacks --stack-name ocp4-disconnected --query 'Stacks[0].Outputs[?OutputKey==`InstallIamUser`].OutputValue' --output text))

aws configure set aws_access_key_id $(echo ${OCP_INSTALL_ACCESS_KEY} | jq '.AccessKey.AccessKeyId') --profile ocp4-install
aws configure set aws_secret_access_key $(echo ${OCP_INSTALL_ACCESS_KEY} | jq '.AccessKey.SecretAccessKey') --profile ocp4-install
aws configure set region $(curl --silent http://169.254.169.254/latest/meta-data/placement/region) --profile ocp4-install

export AWS_PROFILE=ocp4-install
export AWS_EC2_METADATA_DISABLED=true
```

```bash
openshift-install create cluster --dir ~/ocp4-install
```


[ocp_platforms]: https://docs.openshift.com/container-platform/latest/installing/installing-preparing.html#installing-preparing-install-manage
[iam_permissions]: https://docs.openshift.com/container-platform/4.12/installing/installing_aws/installing-aws-account.html#installation-aws-permissions_installing-aws-account
