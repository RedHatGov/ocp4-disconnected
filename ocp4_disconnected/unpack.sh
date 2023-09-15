#!/usr/bin/env bash

set -eux -o pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

CLIENTS_DIR=${SCRIPT_DIR}/clients
IMAGES_DIR=${SCRIPT_DIR}/images
BIN_DIR=${SCRIPT_DIR}/bin
REGISTRY_DIR=${SCRIPT_DIR}/registry

REGISTRY_PASSWORD=$(< /dev/urandom tr -dc A-Za-z0-9 | head -c 30)

###############################################################################
# User Data Prompts
###############################################################################



###############################################################################
# Mirror Registry - Unpack and Install
###############################################################################

mkdir -p ${BIN_DIR}
if [[ -f ${BIN_DIR}/mirror-registry ]]; then
    echo "Mirror registry has already been extracted, skipping"
else
    tar --extract --verbose --directory ${BIN_DIR} --file ${CLIENTS_DIR}/mirror-registry.tar.gz
fi

mkdir -p ${REGISTRY_DIR}
if $(curl --insecure --silent https://$(hostname --fqdn):8443/status); then
    echo "Mirror registry appears to already be running, skipping install"
else
    ${BIN_DIR}/mirror-registry install \
        --quayHostname $(hostname --fqdn) \
        --quayRoot ${REGISTRY_DIR}/quay-install \
        --quayStorage ${REGISTRY_DIR}/quay-storage \
        --pgStorage ${REGISTRY_DIR}/pg-data \
        --initUser openshift \
        --initPassword ${REGISTRY_PASSWORD}
fi
