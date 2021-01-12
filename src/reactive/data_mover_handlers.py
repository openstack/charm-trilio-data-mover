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

import charms_openstack.charm as charm
import charms.reactive as reactive

# This charm's library contains all of the handler code associated with
# trilio_dm
import charm.openstack.trilio_dm as trilio_dm  # noqa

charm.use_defaults(
    "charm.installed", "config.changed", "update-status",
    "shared-db.connected",
)


@reactive.when("shared-db.available")
@reactive.when("amqp.available")
def render_config(*args):
    """Render the configuration for charm when all the interfaces are
    available.
    """
    ceph = reactive.endpoint_from_flag("ceph.available")
    if ceph:
        args = (ceph,) + args
    with charm.provide_charm_instance() as charm_instance:
        charm_instance.render_with_interfaces(args)
        charm_instance.assess_status()
    reactive.set_state("config.rendered")


@reactive.when('shared-db.connected')
def default_setup_database(database):
    """Handle the default database connection setup

    This requires that the charm implements get_database_setup() to provide
    a list of dictionaries;
    [{'database': ..., 'username': ..., 'hostname': ..., 'prefix': ...}]

    The prefix can be missing: it defaults to None.
    """
    with charm.provide_charm_instance() as instance:
        for db in instance.get_database_setup():
            database.configure(**db)
        instance.assess_status()


# NOTE(jamespage): default handler is in api layer which is to much
@reactive.when("amqp.connected")
def default_amqp_connection(amqp):
    """Handle the default amqp connection.

    This requires that the charm implements get_amqp_credentials() to
    provide a tuple of the (user, vhost) for the amqp server
    """
    with charm.provide_charm_instance() as charm_instance:
        user, vhost = charm_instance.get_amqp_credentials()
        amqp.request_access(username=user, vhost=vhost)
        charm_instance.assess_status()


@reactive.when("config.changed.triliovault-pkg-source")
def install_source_changed():
    """Trigger re-install of charm if source configuration options change"""
    reactive.clear_flag("charm.installed")
    reactive.set_flag("upgrade.triliovault")


@reactive.when_not("ceph.access.req.sent")
@reactive.when("ceph.connected")
def ceph_connected(ceph):
    with charm.provide_charm_instance() as charm_instance:
        charm_instance.request_access_to_groups(ceph)
        reactive.set_flag("ceph.access.req.sent")


@reactive.when("ceph.available")
def configure_ceph(ceph):
    with charm.provide_charm_instance() as charm_instance:
        charm_instance.configure_ceph_keyring(ceph.key)
        charm_instance.assess_status()
