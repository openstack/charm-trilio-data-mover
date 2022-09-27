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
import reactive.data_mover_handlers as datamover

import charms_openstack.test_utils as test_utils


_when_args = {}
_when_not_args = {}


def mock_hook_factory(d):
    def mock_hook(*args, **kwargs):
        def inner(f):
            # remember what we were passed.  Note that we can't actually
            # determine the class we're attached to, as the decorator only gets
            # the function.
            try:
                d[f.__name__].append(dict(args=args, kwargs=kwargs))
            except KeyError:
                d[f.__name__] = [dict(args=args, kwargs=kwargs)]
            return f

        return inner

    return mock_hook


class Test(test_utils.PatchHelper):
    @classmethod
    def setUpClass(cls):
        cls._patched_when = mock.patch(
            "charms.reactive.when", mock_hook_factory(_when_args)
        )
        cls._patched_when_started = cls._patched_when.start()
        cls._patched_when_not = mock.patch(
            "charms.reactive.when_not", mock_hook_factory(_when_not_args)
        )
        cls._patched_when_not_started = cls._patched_when_not.start()
        # force requires to rerun the mock_hook decorator:
        # try except is Python2/Python3 compatibility as Python3 has moved
        # reload to importlib.
        try:
            reload(datamover)
        except NameError:
            import importlib

            importlib.reload(datamover)

    @classmethod
    def tearDownClass(cls):
        cls._patched_when.stop()
        cls._patched_when_started = None
        cls._patched_when = None
        cls._patched_when_not.stop()
        cls._patched_when_not_started = None
        cls._patched_when_not = None
        # and fix any breakage we did to the module
        try:
            reload(datamover)
        except NameError:
            import importlib

            importlib.reload(datamover)

    def test_registered_hooks(self):
        # test that the hooks actually registered the relation expressions that
        # are meaningful for this interface: this is to handle regressions.
        # The keys are the function names that the hook attaches to.
        when_patterns = {
            "render_config": ("amqp.available", "shared-db.available"),
            "default_amqp_connection": ("amqp.connected",),
            "default_setup_database": ("shared-db.connected",),
            "install_source_changed": (
                "config.changed.triliovault-pkg-source",
            ),
            "configure_ceph": (
                "ceph.available",
            ),
            "ceph_connected": (
                "ceph.connected",
            ),
            "setup_kernel_modules": (
                "charm.installed",
            ),
        }
        when_not_patterns = {
            "ceph_connected": (
                "ceph.access.req.sent",
            ),
            "setup_kernel_modules": (
                "is-update-status-hook",
            ),
        }
        # check the when hooks are attached to the expected functions
        for t, p in [
            (_when_args, when_patterns),
            (_when_not_args, when_not_patterns),
        ]:
            for f, args in t.items():
                # check that function is in patterns
                self.assertTrue(f in p.keys(), "{} not found".format(f))
                # check that the lists are equal
                lists = []
                for a in args:
                    lists += a["args"][:]
                self.assertEqual(
                    sorted(lists),
                    sorted(p[f]),
                    "{}: incorrect state registration".format(f),
                )
