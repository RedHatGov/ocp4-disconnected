#!/usr/bin/env bash

set -eux

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
# OpenShift Clients
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

###############################################################################
# Populate Mirror Registry
###############################################################################

mkdir -p ${METADATA_DIR}
podman login --username openshift --password $(cat ${REGISTRY_DIR}/registry_password) $(hostname --fqdn):8443

cd ${METADATA_DIR}
oc mirror --from=${LATEST_IMAGES_FILE} docker://$(hostname --fqdn):8443
