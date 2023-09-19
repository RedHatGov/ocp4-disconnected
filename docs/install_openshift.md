# OpenShift 4 Disconnected Bundler Documentation

## Install OpenShift

We're nearly ready to kick off the OpenShift installer. The content bundle contains a convenience script called `unpack.sh` that will facilitate the next few steps in preparation for the installation, namely:
* Extracting nested tar files to access the binaries for tooling within the bundle
* Installing, running, and hydrating the mirror registry with OpenShift release content
* Printing a YAML snippet we'll need for the `install-config.yaml`, which we'll create in the next step

Go ahead and run the script:

```bash
/mnt/ocp4_data/unpack.sh
```

The output should look something like this:
```
The required binaries have been unpacked to /usr/local/bin and the required
container images have been uploaded to the mirror registry. You are ready to
create the install-config.yaml for the target environment.

If you are following along with the walkthrough provided with this tool, check
next steps for how to generate the install-config.yaml for the example environment
that's provided. If you are targeting a different environment, the walkthrough
should also provide some links to the OpenShift documentation for how to
generate the install-config.yaml for the target environment.

Once you have your install-config.yaml created for your target environment,
there's one update to the install-config.yaml we need to make that will tell
the OpenShift installer to use our mirrored content instead of defaulting to
reaching out to the internet for content.

Copy and paste the following blocks of YAML to the end of your install-config.yaml.


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

### Creating the `install-config.yaml`
Next we'll create the `install-config.yaml` which will house the configuration required by `openshift-install` to create our cluster. This process will differ depending on what platform you're installing to. Supported platforms and the accompanying documentation for each can be found in the official documentation [here](https://docs.openshift.com/container-platform/latest/installing/installing-preparing.html#installing-preparing-install-manage). Once you've generated the initial `install-config.yaml`, be sure to make any changes you need in addition to the output from `unpack.sh` above.

For our walkthrough, we're going to proceed with a cluster installation in AWS. 
1. Let's start by creating a workspace on the high side host to house our installation materials:
   ```bash
   mkdir /mnt/ocp4_data/install
   cd /mnt/ocp4_data/install
   ```
2. Then generate an SSH key pair for access to cluster nodes:
   ```bash
   ssh-keygen -f ~/.ssh/ocp4-cluster -q -N ""
   ```
3. Use the following Python code to minify your container registry pull secret. Copy this output to your clipboard, since you'll need it in a moment:
   ```bash
   python3 -c $'import json\nimport sys\nwith open(sys.argv[1], "r") as f: print(json.dumps(json.load(f)))' /run/user/1000/containers/auth.json
   ```
   > For connected installations, you'd use the secret from the Hybrid Cloud Console, but for our use case, the mirror registry is the only one OpenShift will need to authenticate to.
4. Then generate `install-config.yaml`:
   ```bash
   /mnt/ocp4_data/clients/openshift-install create install-config --dir /mnt/ocp4_data/install
   ```

   The OpenShift installer will prompt you for a number of fields; enter the values below:
   * **SSH Public Key**: `/home/ec2-user/.ssh/ocp4-cluster.pub`
     > The SSH public key used to access all nodes within the cluster.
   * **Platform**: `aws`
     > The platform on which the cluster will run.
   * **AWS Access Key ID** and **Secret Access Key**: Enter your AWS credentials from RHDP.
   * **Region**: `us-east-1 (US East (N. Virginia))`
   * **Base Domain**: `sandboxXXXX.opentlc.com`
     > The base domain of the cluster. All DNS records will be sub-domains of this base and will also include the cluster name.
   * **Cluster Name**: `disco`
     > The name of the cluster. This will be used when generating sub-domains.
   * **Pull Secret**: Paste the output from minifying this in Step 3.

   That's it! The installer will generate `install-config.yaml` and drop it in `/mnt/ocp4_data/install` for you.
5. We need to make a couple changes to this config before we kick off the install:
   * Change `publish` from **External** to **Internal**. We're using private subnets to house the cluster, so it won't be publicly accessible.
   * Add the subnet IDs for your private subnets to `platform.aws.subnets`. Otherwise, the installer will create its own VPC and subnets. You can retrieve them by running this command from your high side host:
     ```bash
     aws ec2 describe-subnets | jq '[.Subnets[] | select(.Tags[].Value | contains ("private")).SubnetId] | unique' -r | yq read - -P
     ```
     Then add them to `platform.aws.subnets` in your `install-config.yaml` so that they look something like this:
     ```bash
     ...
     platform:
       aws:
         region: us-east-1
         subnets:
         - subnet-00f28bbc11d25d523
         - subnet-07b4de5ea3a39c0fd
         - subnet-07b4de5ea3a39c0fd
      ...
     ```
   * Modify the `machineNetwork` to match the IPv4 CIDR blocks from the private subnets. Otherwise your control plane and compute nodes will be assigned IP addresses that are out of range and break the install. You can retrieve them by running this command from your workstation:
     ```execute-2
     aws ec2 describe-subnets | jq '[.Subnets[] | select(.Tags[].Value | contains ("private")).CidrBlock] | unique | map("cidr: " + .)' | yq read -P - | sed "s/'//g"  
     ```
     Then use them to **replace the existing** `networking.machineNetwork` **entry** in your `install-config.yaml` so that they look something like this:
     ```bash
     ...
     networking:
       clusterNetwork:
       - cidr: 10.128.0.0/14
         hostPrefix: 23
       machineNetwork:
       - cidr: 10.0.48.0/20
       - cidr: 10.0.64.0/20
       - cidr: 10.0.80.0/20
     ...
     ```
   * Finally, add the snippet output by `unpack.sh` containing the `additionalTrustBundle` and `imageContentSources` to the end of your `install-config.yaml`.
6. Then make a backup of your `install-config.yaml` since the installer will consume (and delete) it:
   ```execute
   cp install-config.yaml install-config.yaml.bak
   ```

### Running the Installation
We're ready to run the install! Let's kick off the cluster installation:
```execute
/mnt/ocp4_data/clients/openshift-install create cluster --dir /mnt/ocp4_data/install --log-level=DEBUG
```
The installation process should take about 30 minutes. If you've done everything correctly, you should see something like this:
```bash
...
INFO Install complete!
INFO To access the cluster as the system:admin user when using 'oc', run 'export KUBECONFIG=/home/myuser/install_dir/auth/kubeconfig'
INFO Access the OpenShift web-console here: https://console-openshift-console.apps.mycluster.example.com
INFO Login to the console with user: "kubeadmin", and password: "password"
INFO Time elapsed: 30m49s
```







