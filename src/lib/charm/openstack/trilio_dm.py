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

import copy
import os

import charmhelpers.core.hookenv as hookenv
import charmhelpers.contrib.openstack.utils as os_utils

import charms.reactive as reactive

import charms_openstack.charm
import charms_openstack.plugins
import charms_openstack.plugins.trilio
import charms_openstack.adapters as os_adapters


charms_openstack.plugins.trilio.make_trilio_handlers()


VALID_BACKUP_TARGETS = ["nfs"]
TV_MOUNTS = "/var/triliovault-mounts"


class DataMoverDBAdapter(os_adapters.DatabaseRelationAdapter):
    """Get database URIs for the two nova databases"""

    @property
    def driver(self):
        return 'mysql+pymysql'

    @property
    def dmapi_uri(self):
        """URI for dmapi DB"""
        return self.get_uri(prefix="dmapi")


@charms_openstack.adapters.config_property
def translated_backup_target_type(cls):
    _type = hookenv.config("backup-target-type").lower()
    if _type == "experimental-s3":
        return 's3'
    return _type


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
        "shared_db": DataMoverDBAdapter,
    }


class TrilioDataMoverBaseCharm(
    charms_openstack.plugins.TrilioVaultSubordinateCharm,
    charms_openstack.plugins.TrilioVaultCharmGhostAction,
    charms_openstack.plugins.BaseOpenStackCephCharm,
):

    release = "queens"
    trilio_release = "4.0"

    service_name = name = "trilio-data-mover"

    adapters_class = DataMoverRelationAdapaters

    data_mover_conf = "/etc/tvault-contego/tvault-contego.conf"
    logrotate_conf = "/etc/logrotate.d/tvault-contego"
    object_store_conf = "/etc/tvault-object-store/tvault-object-store.conf"

    service_type = "data-mover"
    default_service = "tvault-contego"

    required_relations = ["amqp", "shared-db"]

    base_packages = ["tvault-contego", "nfs-common", "contego"]

    # configuration file permissions
    user = "root"
    group = "nova"

    # Setting an empty source_config_key activates special handling of release
    # selection suitable for subordinate charms
    source_config_key = ""

    # Use nova-common package to drive OpenStack Release versioning.
    os_release_pkg = "nova-common"
    package_codenames = os_utils.PACKAGE_CODENAMES

    @property
    def backup_target_type(self):
        # The main purpose of this property is to translate experimental-s3
        # to s3 and s3 to UNKNOWN. This forces the deployer to
        # use 'experimental-s3' for s3 support but the code can stay clean and
        # refer to s3.
        _type = hookenv.config("backup-target-type").lower()
        if _type == 'experimental-s3':
            return 's3'
        if _type == 'nfs':
            return 'nfs'
        return 'UNKNOWN'

    @property
    def packages(self):
        _pkgs = copy.deepcopy(self.base_packages)
        if self.backup_target_type == 's3':
            _pkgs.append('python3-s3-fuse-plugin')
        return _pkgs

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

    def get_database_setup(self):
        return [
            {
                "database": "dmapi",
                "username": "dmapi",
                "prefix": "dmapi",
            },
        ]

    @property
    def services(self):
        if self.backup_target_type == "s3":
            return ["tvault-contego", "tvault-object-store"]
        return ["tvault-contego"]

    @property
    def restart_map(self):
        _restart_map = {
            self.data_mover_conf: self.services,
        }
        if reactive.flags.is_flag_set("ceph.available"):
            _restart_map[self.ceph_conf] = self.services
        if self.backup_target_type == 's3':
            _restart_map[self.object_store_conf] = ['tvault-object-store']
        return _restart_map

    def custom_assess_status_check(self):
        """Check required configuration options are set"""
        check_config_set = []
        if self.backup_target_type == "nfs":
            check_config_set = ['nfs-shares']
        elif self.backup_target_type == "s3":
            check_config_set = [
                "tv-s3-secret-key",
                "tv-s3-access-key",
                "tv-s3-region-name",
                "tv-s3-bucket",
                "tv-s3-endpoint-url"]
        unset_config = [c for c in check_config_set if not hookenv.config(c)]
        if unset_config:
            return "blocked", "{} configuration not set".format(
                ', '.join(unset_config))
        # For s3 support backup-target-type should be set to 'experimental-s3'
        # as s3 support is pre-production. The self.backup_target_type
        # property will do any transaltion needed.
        if self.backup_target_type not in ["nfs", "s3"]:
            return "blocked", "Backup target type not supported"
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

    @classmethod
    def trilio_version_package(cls):
        return 'tvault-contego'


class TrilioDataMoverRockyCharm(TrilioDataMoverBaseCharm):

    release = "rocky"
    trilio_release = "4.0"

    # Python version used to execute installed workload
    python_version = 3

    base_packages = ["python3-tvault-contego", "nfs-common", "contego"]

    @classmethod
    def trilio_version_package(cls):
        return 'python3-tvault-contego'
