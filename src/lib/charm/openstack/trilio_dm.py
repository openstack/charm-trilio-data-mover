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

import collections
import shutil

import charmhelpers.core.hookenv as hookenv
import charmhelpers.fetch as fetch
import charmhelpers.core.host as ch_host

import charms_openstack.charm
import charms_openstack.adapters as os_adapters


DM_USR = "nova"
DM_GRP = "nova"
VALID_BACKUP_TARGETS = ["nfs", "s3"]


class TrilioDataMoverCharm(charms_openstack.charm.OpenStackCharm):

    service_name = name = "trilio-data-mover"

    adapters_class = os_adapters.OpenStackAPIRelationAdapters

    data_mover_conf = "/etc/tvault-contego/tvault-contego.conf"
    logrotate_conf = "/etc/logrotate.d/tvault-contego"

    # First release supported
    release = "stein"

    service_type = "data-mover"
    default_service = "tvault-contego"

    required_relations = ["amqp"]

    package_codenames = {
        "tvault-contego": collections.OrderedDict([("3", "stein")]),
        "python3-tvault-contego": collections.OrderedDict([("3", "stein")]),
    }

    # configuration file permissions
    user = "root"
    group = DM_GRP

    def get_amqp_credentials(self):
        return ("datamover", "openstack")

    def configure_source(self):
        with open("/etc/apt/sources.list.d/"
                  "trilio-gemfury-sources.list", "w") as tsources:
            tsources.write(hookenv.config("triliovault-pkg-source"))
        fetch.apt_update(fatal=True)

    @property
    def packages(self):
        if hookenv.config("python-version") == 2:
            return ["tvault-contego", "nfs-common"]
        return ["python3-tvault-contego", "nfs-common"]

    @property
    def services(self):
        if hookenv.config("backup-target-type") == "s3":
            return ["tvault-contego", "tvault-object-store"]
        return ["tvault-contego"]

    @property
    def restart_map(self):
        return {self.data_mover_conf: self.services}

    # TODO: drop once packaging is updated
    def install(self):
        self.configure_source()
        super().install()
        self.ensure_dirs()
        self.install_files()
        self.configure_nova_user()

    # TODO: drop once packaging is updated
    def upgrade_charm(self):
        super().upgrade_charm()
        self.ensure_dirs()

    # TODO: drop once included in packages
    def ensure_dirs(self):
        """
        Ensures all the required directories are present
        and have appropriate permissions.
        """
        ch_host.mkdir(
            hookenv.config("tv-data-dir"),
            owner=DM_USR,
            group=DM_GRP,
            perms=0o770,
            force=True,
        )
        # TODO: review this?
        # os.system('rm -rf {}'.format(hookenv.config('tv-data-dir-old')))
        ch_host.mkdir(
            hookenv.config("tv-data-dir-old"),
            owner=DM_USR,
            group=DM_GRP,
            perms=0o770,
            force=True,
        )
        ch_host.mkdir(
            "/etc/tvault-contego",
            owner="root",
            group=DM_GRP,
            perms=0o750,
            force=True,
        )

    # TODO: drop once included in packages
    def install_files(self):
        """
        Installs a load of files that should be provided
        by the package
        """
        # "files/trilio/tvault-object-store.service":
        # "/etc/systemd/system",
        _file_map = {
            "files/trilio/tvault-contego.service": "/etc/systemd/system",
            "files/trilio/trilio.filters": "/etc/nova/rootwrap.d",
            "files/trilio/trilio_sudoers": "/etc/sudoers.d/",
            "files/trilio/tvault-contego": "/etc/logrotate.d/",
        }
        for file, target in _file_map.items():
            shutil.copy(file, target)

    # TODO: review why this is required
    def configure_nova_user(self):
        """Add nova user to kvm and disk groups"""
        for grp in ("kvm", "disk"):
            ch_host.add_user_to_group(DM_USR, grp)
