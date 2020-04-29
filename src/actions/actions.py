#!/usr/local/sbin/charm-env python3
# Copyright 2018,2020 Canonical Ltd
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
import sys

# Load modules from $CHARM_DIR/lib
sys.path.append("lib")

from charms.layer import basic

basic.bootstrap_charm_deps()
basic.init_config_states()

import charmhelpers.core.hookenv as hookenv

import charms_openstack.charm

# import the trilio_wlm module to get the charm definitions created.
import charm.openstack.trilio_dm  # noqa


def ghost_share(*args):
    """Ghost mount secondard TV deployment nfs-share
    """
    secondary_nfs_share = hookenv.action_get("nfs-shares")
    with charms_openstack.charm.provide_charm_instance() as trilio_dm_charm:
        trilio_dm_charm.ghost_nfs_share(secondary_nfs_share)


# Actions to function mapping, to allow for illegal python action names that
# can map to a python function.
ACTIONS = {"ghost-share": ghost_share}


def main(args):
    action_name = os.path.basename(args[0])
    try:
        action = ACTIONS[action_name]
    except KeyError:
        return "Action %s undefined" % action_name
    else:
        try:
            action(args)
        except Exception as e:
            hookenv.function_fail(str(e))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
