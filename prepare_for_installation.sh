#!/bin/bash

# Install podman
sudo dnf -y localinstall /mnt/ocp4_data/repos/*.rpm

# Untar mirror registry
tar --extract --verbose --directory /mnt/ocp4_data/clients --file /mnt/ocp4_data/clients/mirror-registry.tar.gz

# Install mirror registry 
#     tucking all the storage in /mnt/ocp4_data/quay for now
#     hardcoding quay password to "discopass"
/mnt/ocp4_data/clients/mirror-registry install --quayHostname $(hostname) --quayRoot /mnt/ocp4_data/quay/quay-install --quayStorage /mnt/ocp4_data/quay/quay-storage --pgStorage /mnt/ocp4_data/quay/pg-data --initPassword discopass

# Login to podman to generate auth file
#    TODO: add quay rootCA to system trust store if we want, or use your own?
podman login -u init -p discopass --tls-verify=false $(hostname):8443

# Move oc and oc-mirror to path
tar --extract --verbose --directory /mnt/ocp4_data/clients --file /mnt/ocp4_data/clients/openshift-client-linux.tar.gz
tar --extract --verbose --directory /mnt/ocp4_data/clients --file /mnt/ocp4_data/clients/openshift-install-linux.tar.gz
tar --extract --verbose --directory /mnt/ocp4_data/clients --file /mnt/ocp4_data/clients/oc-mirror.tar.gz
chmod +x /mnt/ocp4_data/clients/oc-mirror
sudo mv /mnt/ocp4_data/clients/oc* /usr/local/bin/

# Mirror from disk to registry
oc mirror --from=/mnt/ocp4_data/images/mirror_seq1_000000.tar --dest-skip-tls docker://$(hostname):8443
