#!/usr/bin/env bash

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

CLIENTS_DIR=${SCRIPT_DIR}/clients
IMAGES_DIR=${SCRIPT_DIR}/images
BIN_DIR=${SCRIPT_DIR}/bin
REGISTRY_DIR=${SCRIPT_DIR}/registry
METADATA_DIR=${SCRIPT_DIR}/metadata

REGISTRY_PASSWORD=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 30)
LATEST_IMAGES_FILE=$(find ${IMAGES_DIR} -name 'mirror_seq*.tar' | sort -Vr | head -n 1)

###############################################################################
# User Data Prompts
###############################################################################



###############################################################################
# Mirror Registry
###############################################################################

mkdir -p ${BIN_DIR}
if [[ -f ${BIN_DIR}/mirror-registry ]]; then
    echo "Mirror registry has already been extracted, skipping"
else
    tar --extract --verbose --directory ${BIN_DIR} --file ${CLIENTS_DIR}/mirror-registry.tar.gz
fi

mkdir -p ${REGISTRY_DIR}
if [[ -d ${REGISTRY_DIR}/quay-install ]]; then
    echo "Mirror registry appears to already be running, skipping install"
else
    echo ${REGISTRY_PASSWORD} > ${REGISTRY_DIR}/registry_password

    cd ${REGISTRY_DIR}
    ${BIN_DIR}/mirror-registry install \
        --quayHostname $(hostname --fqdn) \
        --quayRoot ${REGISTRY_DIR}/quay-install \
        --quayStorage ${REGISTRY_DIR}/quay-storage \
        --pgStorage ${REGISTRY_DIR}/pg-data \
        --initUser openshift \
        --initPassword ${REGISTRY_PASSWORD}
fi

if [[ ! -f /etc/pki/ca-trust/source/anchors/quay_mirror_registry_ca.pem ]]; then
    sudo cp ${REGISTRY_DIR}/quay-install/quay-rootCA/rootCA.pem /etc/pki/ca-trust/source/anchors/quay_mirror_registry_ca.pem
    sudo update-ca-trust extract
fi

###############################################################################
# Clients
###############################################################################

cd ${SCRIPT_DIR}
if [[ ! -f /usr/local/bin/oc ]]; then
    sudo tar --extract --verbose --directory /usr/local/bin --file ${CLIENTS_DIR}/openshift-client-linux.tar.gz oc kubectl
    sudo chmod +x /usr/local/bin/oc /usr/local/bin/kubectl
fi

if [[ ! -f /usr/local/bin/oc-mirror ]]; then
    sudo tar --extract --verbose --directory /usr/local/bin --file ${CLIENTS_DIR}/oc-mirror.tar.gz oc-mirror
    sudo chmod +x /usr/local/bin/oc-mirror
fi

if [[ ! -f /usr/local/bin/openshift-install ]]; then
    sudo tar --extract --verbose --directory /usr/local/bin --file ${CLIENTS_DIR}/openshift-install-linux.tar.gz openshift-install
    sudo chmod +x /usr/local/bin/openshift-install
fi

if [[ ! -f /usr/local/bin/jq ]]; then
    sudo cp ${CLIENTS_DIR}/jq /usr/local/bin/jq
    sudo chmod +x /usr/local/bin/jq
fi

if [[ ! -f /usr/local/bin/yq ]]; then
    sudo cp ${CLIENTS_DIR}/yq /usr/local/bin/yq
    sudo chmod +x /usr/local/bin/yq
fi

###############################################################################
# Populate Mirror Registry
###############################################################################

mkdir -p ${METADATA_DIR}
podman login --username openshift --password $(cat ${REGISTRY_DIR}/registry_password) $(hostname --fqdn):8443

cd ${METADATA_DIR}

set +e
oc mirror --from=${LATEST_IMAGES_FILE} docker://$(hostname --fqdn):8443 2>/tmp/oc-mirror-error.log

if [[ $? != 0 ]]; then
    if ! grep --quiet 'expecting imageset with prefix mirror_seq' /tmp/oc-mirror-error.log; then
        rm -f /tmp/oc-mirror-error.log
        exit 1
    fi
fi

set -e
cat /tmp/oc-mirror-error.log
rm -f /tmp/oc-mirror-error.log

for results_dir in $(find ${METADATA_DIR}/oc-mirror-workspace -type d -name 'results-*' | sort -Vr); do
    if [[ -f ${results_dir}/imageContentSourcePolicy.yaml ]]; then
        LATEST_ICSP_FILE=${results_dir}/imageContentSourcePolicy.yaml
        break
    fi
done

###############################################################################
# Install Config
###############################################################################

yq eval --null-input '{"additionalTrustBundle": "'"$(</mnt/ocp4_data/registry/quay-install/quay-rootCA/rootCA.pem)"'"}' > ${REGISTRY_DIR}/install_config_registry.yaml
cat ${LATEST_ICSP_FILE} | yq eval --no-doc '.spec.repositoryDigestMirrors' | yq eval '{"imageContentSources": . }' >> ${REGISTRY_DIR}/install_config_registry.yaml

echo
echo
cat << EOF
The binaries have been unpacked to /usr/local/bin and the container images have
been uploaded to the mirror registry. You are ready to create the
install-config.yaml for the target environment.

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
This output has also been saved to ${REGISTRY_DIR}/install_config_registry.yaml
EOF
echo
echo

cat ${REGISTRY_DIR}/install_config_registry.yaml

echo
echo
