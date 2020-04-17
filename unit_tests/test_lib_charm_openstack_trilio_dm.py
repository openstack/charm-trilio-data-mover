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


# TODO: refactor into a layer/module
class TestTrilioDataMoverCharmGhostShareAction(Helper):

    _nfs_shares = "10.20.30.40:/srv/trilioshare"
    _ghost_shares = "50.20.30.40:/srv/trilioshare"

    def setUp(self):
        super().setUp()
        self.patch_object(trilio_dm.hookenv, "config")
        self.patch_object(trilio_dm.host, "mounts")
        self.patch_object(trilio_dm.host, "mount")
        self.patch_object(trilio_dm.os.path, "exists")
        self.patch_object(trilio_dm.os, "mkdir")

        self.trilio_wlm_charm = trilio_dm.TrilioDataMoverCharm()
        self._nfs_path = os.path.join(
            trilio_dm.TV_MOUNTS,
            self.trilio_wlm_charm._encode_endpoint(self._nfs_shares),
        )
        self._ghost_path = os.path.join(
            trilio_dm.TV_MOUNTS,
            self.trilio_wlm_charm._encode_endpoint(self._ghost_shares),
        )

    def test_ghost_share(self):
        self.config.return_value = self._nfs_shares
        self.mounts.return_value = [
            ["/srv/nova", "/dev/sda"],
            [self._nfs_path, self._nfs_shares],
        ]
        self.exists.return_value = False
        self.trilio_wlm_charm.ghost_nfs_share(self._ghost_shares)
        self.exists.assert_called_once_with(self._ghost_path)
        self.mkdir.assert_called_once_with(self._ghost_path)
        self.mount.assert_called_once_with(
            self._nfs_path, self._ghost_path, options="bind"
        )

    def test_ghost_share_already_bound(self):
        self.config.return_value = self._nfs_shares
        self.mounts.return_value = [
            ["/srv/nova", "/dev/sda"],
            [self._nfs_path, self._nfs_shares],
            [self._ghost_path, self._nfs_shares],
        ]
        with self.assertRaises(trilio_dm.GhostShareAlreadyMountedException):
            self.trilio_wlm_charm.ghost_nfs_share(self._ghost_shares)
        self.mount.assert_not_called()

    def test_ghost_share_nfs_unmounted(self):
        self.config.return_value = self._nfs_shares
        self.mounts.return_value = [["/srv/nova", "/dev/sda"]]
        self.exists.return_value = False
        with self.assertRaises(trilio_dm.NFSShareNotMountedException):
            self.trilio_wlm_charm.ghost_nfs_share(self._ghost_shares)
        self.mount.assert_not_called()
