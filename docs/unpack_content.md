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

After extracting the `ocp4_bundle.tar` file, we now have the content we need to
install OpenShift in a disconnected environment. But before we can do that, we
need to put everything in the right place. Also included in the tar file that
we unpacked is a script named `unpack.sh` that automates this for us.

We'll run the script and wait for it to finish. During this process it will
unpack the binaries needed and put them in the appropriate places on the
filesystem (e.g. `/usr/local/bin`), it will deploy the OpenShift Mirror
Registry, and then it will populate the mirror registry with the container
images.

```bash
/mnt/ocp4_data/unpack.sh
```

Once the `unpack.sh` script finishes, it will output a configuration that you
will need to copy and paste to the end of your `install-config.yaml` that's
used to install OpenShift. We'll create the `install-config.yaml` in the next
section and those instructions will show you where to put that configuration.

> [!NOTE]
> If you lose the confirmation output at any point, you can run `unpack.sh`
> again and it will skip things it's already done and output the configuration
> output again.

Example output:

```text
additionalTrustBundle: |-
  -----BEGIN CERTIFICATE-----
  MIIEATCCAumgAwIBAgIUG5laoRL+8bfF2DPxJPzR6mAN2SwwDQYJKoZIhvcNAQEL
  BQAwgYIxCzAJBgNVBAYTAlVTMQswCQYDVQQIDAJWQTERMA8GA1UEBwwITmV3IFlv
  cmsxDTALBgNVBAoMBFF1YXkxETAPBgNVBAsMCERpdmlzaW9uMTEwLwYDVQQDDChp
  cC0xMC0wLTQ5LTQyLnVzLWVhc3QtMi5jb21wdXRlLmludGVybmFsMB4XDTIzMDkx
  NTE4MTA1OFoXDTI2MDcwNTE4MTA1OFowgYIxCzAJBgNVBAYTAlVTMQswCQYDVQQI
  DAJWQTERMA8GA1UEBwwITmV3IFlvcmsxDTALBgNVBAoMBFF1YXkxETAPBgNVBAsM
  CERpdmlzaW9uMTEwLwYDVQQDDChpcC0xMC0wLTQ5LTQyLnVzLWVhc3QtMi5jb21w
  dXRlLmludGVybmFsMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA6hqU
  hh1uEH05SihdcdEB4qBo3sbpm5rt3XzfB5U4Q1zJcSNqGFxcsHy4M4tgH6WRaSco
  E0VqjlnuxzmOkBAnbGnCNHHJxRmRakm3CMBmaK6zA+/k4RjhVzXnaFqlXeditSx3
  d1rsd7FMdbWdNgrQaHPIuV2rtKFU9/bI0y4S+TH1GUNfakSTQzo1knbB4vC81DFZ
  o8wC9M9d3T9rGIeWtNPWD3kIYLSwhw8Cdk0Dms3SMhBnhUWLQq5zJmj0gK1SELH6
  2ZzNVESRpmMcDeiqEaaLUIQRDDrpmHECweNX+PQqyeopxxhLPIRB2WMJEbaeNtXI
  XgVe8vD9h5VdMSOLdQIDAQABo20wazALBgNVHQ8EBAMCAuQwEwYDVR0lBAwwCgYI
  KwYBBQUHAwEwMwYDVR0RBCwwKoIoaXAtMTAtMC00OS00Mi51cy1lYXN0LTIuY29t
  cHV0ZS5pbnRlcm5hbDASBgNVHRMBAf8ECDAGAQH/AgEBMA0GCSqGSIb3DQEBCwUA
  A4IBAQCCwlTbg7m/D3Akp5/bufQyL751x2UTxqY3dPUFQXrMh+hUaoFaOd9NZdE1
  laiTMTmiXhatnpSoh3tvKpFqy41GPqEr+jRPQ/J1H8Luok5k9ud58ikn7PsbtZpW
  sXxQGJb0dQouPzQNwTWXtvtFtP9ydrB9rRQGh+x7Je4+uwmz9w31e8uyEudrw0sb
  iTUDpftyGYJeTBDJySEZNF7jGABEny2jPVWnG3rXtEj2Lkt4ZkwixLTHFYZtbfp+
  W/vAur1bnkbtm1p21SkeI/sE8D2KXLynPkaXfYIbF4bgs0N7KCfRLQXgUbwrIdI5
  GwgfEglJ+zHNyH64ixCBXEJqy4ti
  -----END CERTIFICATE-----
imageContentSources:
  - mirrors:
      - ip-10-0-49-42.us-east-2.compute.internal:8443/ubi8
    source: registry.access.redhat.com/ubi8
  - mirrors:
      - ip-10-0-49-42.us-east-2.compute.internal:8443/openshift/release
    source: quay.io/openshift-release-dev/ocp-v4.0-art-dev
  - mirrors:
      - ip-10-0-49-42.us-east-2.compute.internal:8443/openshift/release-images
    source: quay.io/openshift-release-dev/ocp-release
```

[<< Back: Bundle Content](bundle_content.md) - [Next: Install OpenShift >>](install_openshift.md)
