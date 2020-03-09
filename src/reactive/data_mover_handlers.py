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
    "charm.installed",
    "config.changed",
    "update-status",
)


@reactive.when("amqp.available")
def render_config(*args):
    """Render the configuration for charm when all the interfaces are
    available.
    """
    with charm.provide_charm_instance() as charm_class:
        charm_class.render_with_interfaces(args)
        charm_class.assess_status()
    reactive.set_state("config.rendered")


# NOTE(jamespage): default handler is in api layer which is to much
@reactive.when('amqp.connected')
def default_amqp_connection(amqp):
    """Handle the default amqp connection.

    This requires that the charm implements get_amqp_credentials() to
    provide a tuple of the (user, vhost) for the amqp server
    """
    with charm.provide_charm_instance() as instance:
        user, vhost = instance.get_amqp_credentials()
        amqp.request_access(username=user, vhost=vhost)
        instance.assess_status()