# OpenShift 4 Disconnected Bundler Documentation

## Unpack Content

Now that our content has been uploaded to the S3 bucket, we are ready to pull
it down to the host in the disconnected environment and unpack it.

> [!NOTE]
> If you're still connected to the Jump host from the previous steps, `exit`
> from the SSH connection so that you are back to your primary terminal prompt
> on your machine.

Start by connecting to the High Side host via SSH. Since this host is in the
disconnected environment, it is not directly accesible and we will need to
connect to it through the Jump host. You will need the public IP of the Jump
host and the private IP of the High Side host from the outputs captured during
the environment prep stage or you can use the command below as a convenience.

```bash
export JUMP_HOST_PUBLIC_IP=$(aws cloudformation describe-stacks --stack-name ocp4-disconnected --query 'Stacks[0].Outputs[?OutputKey==`JumpInstancePublicIp`].OutputValue' --output text)
export HIGHSIDE_HOST_PRIVATE_IP=$(aws cloudformation describe-stacks --stack-name ocp4-disconnected --query 'Stacks[0].Outputs[?OutputKey==`HighSideInstancePrivateIp`].OutputValue' --output text)

ssh-add ~/.ssh/ocp4-disconnected
ssh -J ec2-user@${JUMP_HOST_PUBLIC_IP} ec2-user@${HIGHSIDE_HOST_PRIVATE_IP}
```

We are now ready to pull `ocp4_bundle.tar` from our S3 bucket to our High Side
host. To reiterate again, in a real environment we would follow the approved
process for transferring content to our disconnected environment, but for this
walkthrough we will be using an S3 bucket. You can grab the name of the S3
bucket from the outputs captured during the environment prep stage or you can
use the command below as a convenience.

```bash
export S3_TRANSER_BUCKET=$(aws cloudformation describe-stacks --stack-name ocp4-disconnected --query 'Stacks[0].Outputs[?OutputKey==`S3TransferBucket`].OutputValue' --output text)

aws s3 cp s3://${S3_TRANSER_BUCKET}/ocp4_bundle.tar /mnt/ocp4_data
```

We will unpack the tar file next so that we can get access to the content
inside.

```bash
tar --extract --verbose --directory /mnt/ocp4_data --file /mnt/ocp4_data/ocp4_bundle.tar
```

[<< Back: Bundle Content](bundle_content.md) - [Next: Install OpenShift >>](install_openshift.md)
