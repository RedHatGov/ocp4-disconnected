#!/usr/bin/env bash

echo "AWS_PROFILE for AWS commercial regions:"
read aws_profile_commercial

echo "AWS_PROFILE for AWS GovCloud regions:"
read aws_profile_govcloud

rhel_version="RHEL-8.8"
profiles=("${aws_profile_commercial}" "${aws_profile_govcloud}")

echo
echo
echo "Mappings:"
echo "  RegionMap:"

for profile in ${profiles[@]}; do
    export AWS_PROFILE=${profile}

    regions=$(aws ec2 describe-regions --output text --query 'Regions[*].RegionName')

    for region in $regions; do
        ami=$(aws ec2 describe-images --region ${region} --filters "Name=name,Values='${rhel_version}*-Hourly*'" "Name=architecture,Values=x86_64" | jq -r '.Images |= sort_by(.CreationDate) | .Images | reverse | .[0].ImageId')
        echo "    ${region}:"
        echo "      ami: ${ami}"
    done
done
