# OpenShift 4 Disconnected Bundler Documentation

The following documentation will walk you through how to use this tool.
Included in this repository is a CloudFormation script that will create a
simulated disconnected environment that you can use to try it out. To assist in
illustrating how to use this tool, this documentation will take advantage of an
environment created using that CloudFormation script.

At a high level, the process for using this tool to deploy an OpenShift cluster
in a disconnected environment looks like this:

- Using a host with access to the internet, run this tool to download all of
  the content required for an OpenShift install and bundle it
- Transfer the generated content bundle to the disconnected environment (we
  will use S3 in our example)
- Create a RHEL host in the disconnected environment and pull the bundle of
  content to the host
- Unpack the bundle and run the provided script to stand up the required
  supporting infrastructure (e.g. container registry) and generate the
  configuration required to install in a disconnected environment
- Run the OpenShift installer after adding the required configuration

## Prepare Environment

As mentioned above, we are going to create a simulated disconnected environment
in AWS using a CloudFormation script provided in this repository.

Export the required environment variables to setup your AWS credentials and region.

```bash
# If you do not have AWS credentials configured, export these instead:
# export AWS_ACCESS_KEY_ID=
# export AWS_SECRET_ACCESS_KEY=
export AWS_PROFILE=rhdp
export AWS_REGION=us-east-2
```

The only required parameter for the CloudFormation script is the name of the
key pair you wish to use to be able to SSH into the EC2 instances that are
created. If you do not already have a key pair, you can easily create one using
your existing SSH public key.

```bash
ssh-keygen -q -N '' -f ~/.ssh/ocp4-disconnected

aws ec2 import-key-pair --key-name ocp4-disconnected --public-key-material fileb://~/.ssh/ocp4-disconnected.pub
```

Once your key pair is in place, create the simulated disconnected environment
using the CloudFormation script.

```bash
curl https://raw.githubusercontent.com/jaredhocutt/ocp4-disconnected/main/hack/cloudformation.yaml -o /tmp/ocp4-disconnected-cf.yaml

aws cloudformation create-stack \
    --stack-name ocp4-disconnected \
    --template-body file:///tmp/ocp4-disconnected-cf.yaml \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameters "ParameterKey=KeyName,ParameterValue=ocp4-disconnected"
```

Wait for the CloudFormation stack to finish deploying. Once the output is
`CREATE_COMPLETE`, you can use _Ctrl-C_ to exit the `watch` command. It usually
takes in the ballpark of 5-6 minutes to deploy the entire stack.

```bash
watch -n 10 aws cloudformation describe-stacks --stack-name ocp4-disconnected --query 'Stacks[0].StackStatus'
```

Now that the CloudFormation stack has finished deploying, we can capture the
output in order to get the IP addresses we need in order to connect to the EC2
instances that were created.

```bash
aws cloudformation describe-stacks --stack-name ocp4-disconnected --query 'Stacks[0].Outputs'
```

However, as we go through this walkthrough, the commands to grab the value from
the outputs will be provided.

TODO: Insert diagram of VPC + EC2

[Next: Bundle Content >>](bundle_content.md)
