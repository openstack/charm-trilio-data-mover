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


import mock

import charm.openstack.trilio_dm as trilio_dm
import charms_openstack.test_utils as test_utils


class Helper(test_utils.PatchHelper):
    def setUp(self):
        super().setUp()
        self.patch_release(trilio_dm.TrilioDataMoverCharm.release)


class TestTrilioDataMoverCharms(Helper):
    def test_packages_py2(self):
        dm_charm = trilio_dm.TrilioDataMoverCharm()
        self.patch_object(trilio_dm.hookenv, "config")
        self.config.return_value = 2
        self.assertEqual(dm_charm.packages, ["tvault-contego", "nfs-common"])

    def test_packages_py3(self):
        dm_charm = trilio_dm.TrilioDataMoverCharm()
        self.patch_object(trilio_dm.hookenv, "config")
        self.config.return_value = 3
        self.assertEqual(
            dm_charm.packages, ["python3-tvault-contego", "nfs-common"]
        )

    def test_services_nfs(self):
        dm_charm = trilio_dm.TrilioDataMoverCharm()
        self.patch_object(trilio_dm.hookenv, "config")
        self.config.return_value = "nfs"
        self.assertEqual(dm_charm.services, ["tvault-contego"])

    def test_services_s3(self):
        dm_charm = trilio_dm.TrilioDataMoverCharm()
        self.patch_object(trilio_dm.hookenv, "config")
        self.config.return_value = "s3"
        self.assertEqual(
            dm_charm.services, ["tvault-contego", "tvault-object-store"]
        )
