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

import base64
import os

import charmhelpers.core.hookenv as hookenv
import charmhelpers.core.host as host
import charmhelpers.fetch as fetch

import charms_openstack.charm
import charms_openstack.adapters as os_adapters

# select the default release function
charms_openstack.charm.use_defaults('charm.default-select-release')

VALID_BACKUP_TARGETS = ["nfs"]
TV_MOUNTS = "/var/triliovault-mounts"


class NFSShareNotMountedException(Exception):
    """Signal that the trilio nfs share is not mount"""

    pass


class GhostShareAlreadyMountedException(Exception):
    """Signal that a ghost share is already mounted"""

    pass


class TrilioDataMoverBaseCharm(charms_openstack.charm.OpenStackCharm):

    release = "queens"

    service_name = name = "trilio-data-mover"

    adapters_class = os_adapters.OpenStackAPIRelationAdapters

    data_mover_conf = "/etc/tvault-contego/tvault-contego.conf"
    logrotate_conf = "/etc/logrotate.d/tvault-contego"

    service_type = "data-mover"
    default_service = "tvault-contego"

    required_relations = ["amqp"]

    packages = ["tvault-contego", "nfs-common"]

    # configuration file permissions
    user = "root"
    group = "nova"

    def get_amqp_credentials(self):
        return ("datamover", "openstack")

    def configure_source(self):
        with open(
            "/etc/apt/sources.list.d/" "trilio-gemfury-sources.list", "w"
        ) as tsources:
            tsources.write(hookenv.config("triliovault-pkg-source"))
        fetch.apt_update(fatal=True)

    @property
    def services(self):
        if hookenv.config("backup-target-type") == "s3":
            return ["tvault-contego", "tvault-object-store"]
        return ["tvault-contego"]

    @property
    def restart_map(self):
        return {self.data_mover_conf: self.services}

    def install(self):
        self.configure_source()
        super().install()

    def _encode_endpoint(self, backup_endpoint):
        """base64 encode an backup endpoint for cross mounting support"""
        return base64.b64encode(backup_endpoint.encode()).decode()

    # TODO: refactor into a layer/module
    def ghost_nfs_share(self, ghost_share):
        """Bind mount the local units nfs share to another sites location

        :param ghost_share: NFS share URL to ghost
        :type ghost_share: str
        """
        nfs_share_path = os.path.join(
            TV_MOUNTS, self._encode_endpoint(hookenv.config("nfs-shares"))
        )
        ghost_share_path = os.path.join(
            TV_MOUNTS, self._encode_endpoint(ghost_share)
        )

        current_mounts = [mount[0] for mount in host.mounts()]

        if nfs_share_path not in current_mounts:
            # Trilio has not mounted the NFS share so return
            raise NFSShareNotMountedException(
                "nfs-shares ({}) not mounted".format(
                    hookenv.config("nfs-shares")
                )
            )

        if ghost_share_path in current_mounts:
            # bind mount already setup so return
            raise GhostShareAlreadyMountedException(
                "ghost mountpoint ({}) already bound".format(ghost_share_path)
            )

        if not os.path.exists(ghost_share_path):
            os.mkdir(ghost_share_path)

        host.mount(nfs_share_path, ghost_share_path, options="bind")

    def custom_assess_status_check(self):
        """Check required configuration options are set"""
        if not hookenv.config("nfs-shares"):
            return "blocked", "nfs-shares configuration not set"
        return None, None


class TrilioDataMoverRockyCharm(TrilioDataMoverBaseCharm):

    release = "rocky"

    packages = ["python3-tvault-contego", "nfs-common"]
