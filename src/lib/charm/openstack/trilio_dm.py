# Copyright 2020 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import charmhelpers.core.hookenv as hookenv
import charmhelpers.contrib.openstack.utils as os_utils

import charms.reactive as reactive

import charms_openstack.charm
import charms_openstack.plugins
import charms_openstack.adapters as os_adapters

# select the default release function
charms_openstack.charm.use_defaults("charm.default-select-release")

VALID_BACKUP_TARGETS = ["nfs"]
TV_MOUNTS = "/var/triliovault-mounts"


@os_adapters.config_property
def ceph_dir(ceph):
    return os.path.join("/var/lib/charm", hookenv.service_name())


@os_adapters.config_property
def rbd_user(ceph):
    return hookenv.service_name()


class NFSShareNotMountedException(Exception):
    """Signal that the trilio nfs share is not mount"""

    pass


class GhostShareAlreadyMountedException(Exception):
    """Signal that a ghost share is already mounted"""

    pass


class DataMoverRelationAdapaters(os_adapters.OpenStackAPIRelationAdapters):
    """
    Adapters collection for TrilioVault data mover
    """

    relation_adapters = {
        "ceph": charms_openstack.plugins.CephRelationAdapter,
        "amqp": os_adapters.RabbitMQRelationAdapter,
    }


class TrilioDataMoverBaseCharm(
    charms_openstack.plugins.TrilioVaultSubordinateCharm,
    charms_openstack.plugins.TrilioVaultCharmGhostAction,
    charms_openstack.plugins.BaseOpenStackCephCharm,
):

    release = "queens"

    service_name = name = "trilio-data-mover"

    adapters_class = DataMoverRelationAdapaters

    data_mover_conf = "/etc/tvault-contego/tvault-contego.conf"
    logrotate_conf = "/etc/logrotate.d/tvault-contego"

    service_type = "data-mover"
    default_service = "tvault-contego"

    required_relations = ["amqp"]

    packages = ["tvault-contego", "nfs-common"]

    # configuration file permissions
    user = "root"
    group = "nova"

    # Setting an empty source_config_key activates special handling of release
    # selection suitable for subordinate charms
    source_config_key = ""

    # Use nova-common package to drive OpenStack Release versioning.
    release_pkg = "nova-common"
    package_codenames = os_utils.PACKAGE_CODENAMES

    # Set ceph keyring prefix to charm specific location
    @property
    def ceph_keyring_path_prefix(self):
        return os.path.join("/var/lib/charm", hookenv.service_name())

    @property
    def ceph_conf(self):
        return os.path.join(self.ceph_keyring_path, "ceph.conf")

    def configure_ceph_keyring(self, key, cluster_name=None):
        """Creates or updates a Ceph keyring file.

        :param key: Key data
        :type key: str
        :param cluster_name: (Optional) Name of Ceph cluster to operate on.
                             Defaults to value of ``self.ceph_cluster_name``.
        :type cluster_name: str
        :returns: Absolute path to keyring file
        :rtype: str
        :raises: subprocess.CalledProcessError, OSError
        """
        keyring_absolute_path = super().configure_ceph_keyring(
            key, cluster_name
        )
        # TODO: add support for custom permissions into charms.openstack
        if os.path.exists(keyring_absolute_path):
            # NOTE: triliovault access the keyring as the nova user, so
            #       set permissions so it can do this.
            os.chmod(keyring_absolute_path, 0o640)
            ceph_keyring = os.path.join(
                "/etc/ceph", os.path.basename(keyring_absolute_path)
            )
            # NOTE: triliovault needs a keyring in /etc/ceph as well as in the
            #       charm specific location for qemu commands to work
            if not os.path.exists(ceph_keyring):
                os.symlink(keyring_absolute_path, ceph_keyring)
        # NOTE: ensure /var/lib/charm is world readable - this will be the
        #       case with Python >= 3.7 but <= 3.6 has different behaviour
        os.chmod('/var/lib/charm', 0o755)
        return keyring_absolute_path

    def get_amqp_credentials(self):
        return ("datamover", "openstack")

    @property
    def services(self):
        if hookenv.config("backup-target-type") == "s3":
            return ["tvault-contego", "tvault-object-store"]
        return ["tvault-contego"]

    @property
    def restart_map(self):
        if reactive.flags.is_flag_set("ceph.available"):
            return {
                self.data_mover_conf: self.services,
                self.ceph_conf: self.services,
            }
        return {
            self.data_mover_conf: self.services,
        }

    def custom_assess_status_check(self):
        """Check required configuration options are set"""
        if not hookenv.config("nfs-shares"):
            return "blocked", "nfs-shares configuration not set"
        return None, None

    def request_access_to_groups(self, ceph):
        """Request access to pool types needed for dm operation.

        :param ceph: ceph interface
        :type ceph: ceph-interface:CephClientRequires
        """
        for ceph_group in ("volumes", "images", "vms"):
            ceph.request_access_to_group(
                name=ceph_group,
                object_prefix_permissions={"class-read": ["rbd_children"]},
                permission="rwx",
            )


class TrilioDataMoverRockyCharm(TrilioDataMoverBaseCharm):

    release = "rocky"

    packages = ["python3-tvault-contego", "nfs-common"]
