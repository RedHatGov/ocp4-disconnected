# OpenShift 4 Disconnected Bundler Documentation

## Unpack Content

Now that our content has been uploaded to the S3 bucket, we are ready to pull it down to the host in the disconnected environment and unpack it.

Start by connecting to the High Side host via SSH. Since this host is in the
disconnectede environment, it is not directly accesible and we will need to
connect to it through the Jump host. You will need the public IP of the Jump
host and the private IP of the High Side host from the outputs captured during
the environment prep stage or you can use the command below as a convenience.

```bash
export JUMP_HOST_PUBLIC_IP=$(aws cloudformation describe-stacks --stack-name ocp4-disconnected --query 'Stacks[0].Outputs[?OutputKey==`JumpInstancePublicIp`].OutputValue' --output text)
export HIGHSIDE_HOST_PRIVATE_IP=$(aws cloudformation describe-stacks --stack-name ocp4-disconnected --query 'Stacks[0].Outputs[?OutputKey==`HighSideInstancePrivateIp`].OutputValue' --output text)

ssh-add ~/.ssh/ocp4-disconnected
ssh -J ec2-user@${JUMP_HOST_PUBLIC_IP} ec2-user@${HIGHSIDE_HOST_PRIVATE_IP}
```
