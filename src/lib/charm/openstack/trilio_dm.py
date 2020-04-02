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
import collections

import charmhelpers.core.hookenv as hookenv
import charmhelpers.fetch as fetch

import charms_openstack.charm
import charms_openstack.adapters as os_adapters


VALID_BACKUP_TARGETS = ["nfs"]


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

    def _encode_endpoint(self, backup_endpoint):
        """base64 encode an backup endpoint for cross mounting support"""
        return base64.b64encode(backup_endpoint.encode()).decode()

    def install(self):
        self.configure_source()
        super().install()
