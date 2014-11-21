# -*- coding: utf8 -*-
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import collections
import json
import logging


from django.conf import settings
from django.utils.translation import ugettext_lazy as _
import horizon.messages
from horizon import tabs
import requests
import requests_oauthlib
from tuskar_ui import api
from tuskar_ui.infrastructure.nodes import tabs as nodes_tabs

from tuskar_sat_ui.nodes import tables


SAT_HOST_PARAM = 'SatelliteHost'
SAT_AUTH_PARAM = 'SatelliteAuth'
SAT_ORG_PARAM = 'SatelliteOrg'
VERIFY_SSL = not getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
LOG = logging.getLogger('tuskar_sat_ui')
ErrataItem = collections.namedtuple('ErrataItem', [
    'title',
    'type',
    'id',
    'issued',
])


class Error(Exception):
    pass


class NoConfigError(Error):
    """Failed to find the Satellite configuration in Heat parameters."""

    def __init__(self, param=None, *args, **kwargs):
        super(NoConfigError, self).__init__(*args, **kwargs)
        self.param = param


class NodeNotFound(Error):
    """Failed to find the Satellite node."""


class BadAuthError(Error):
    """Unknown authentication method for Satellite."""

    def __init__(self, auth=None, *args, **kwargs):
        super(BadAuthError, self).__init__(*args, **kwargs)
        self.auth = auth


class NoErrataError(Error):
    """There is no errata for that node."""


def _get_satellite_config(parameters):
    """Find the Satellite configuration data.

    The configuration data is store in Heat as parameters.  They may be
    stored directly as Heat parameters, or in a the JSON structure stored
    in ExtraConfig.
    """

    param = 'Satellite'
    try:
        config = parameters[param]
    except KeyError:
        try:
            extra = json.loads(parameters['compute-1::ExtraConfig'])
            config = extra[param]
        except (KeyError, ValueError, TypeError):
            raise NoConfigError(param, 'Parameter %r missing.' % param)

    for param in [SAT_HOST_PARAM, SAT_AUTH_PARAM, SAT_ORG_PARAM]:
        if param not in config:
            raise NoConfigError(param, 'Parameter %r missing.' % param)

    host = config[SAT_HOST_PARAM]
    host = host.strip('/')  # Get rid of any trailing slash in the host url

    try:
        auth = config[SAT_AUTH_PARAM].split(':', 2)
    except ValueError:
        raise BadAuthError(auth=config[SAT_AUTH_PARAM])
    if auth[0] == 'oauth':
        auth = requests_oauthlib.OAuth1(auth[1], auth[2])
    elif auth[0] == 'basic':
        auth = auth[1], auth[2]
    else:
        raise BadAuthError(auth=auth[0])
    organization = config[SAT_ORG_PARAM]
    return host, auth, organization


def _get_stack(request):
    """Find the stack."""

    # TODO(rdopiera) We probably should use the StackMixin instead.
    try:
        plan = api.tuskar.Plan.get_the_plan(request)
        stack = api.heat.Stack.get_by_plan(request, plan)
    except Exception as e:
        LOG.exception(e)
        horizon.messages.error(request, _("Could not retrieve errata."))
        return None
    return stack


def _find_uuid_by_mac(host, auth, organization, addresses):
    """Pick up the UUID from the MAC address.

    This makes no sense, as we need both MAC address and the interface, and
    we don't have the interface, so we need to make multiple slow searches.
    If the Satellite UUID isn't the same as this one, and it probably
    isn't, we need to store a mapping somewhere.
    """

    url = '{host}/katello/api/v2/systems'.format(host=host)
    for mac in addresses:
        for interface in ['eth0', 'eth1', 'en0', 'en1']:
            q = 'facts.net.interface.{iface}.mac_address:{mac}'.format(
                iface=interface, mac=mac)
            params = {'search': q, 'organization_id': organization}
            r = requests.get(url, params=params, auth=auth,
                             verify=VERIFY_SSL)
            r.raise_for_status()  # Raise an error if the request failed
            contexts = r.json()['results']
            if contexts:
                return contexts[0]['uuid']
    raise NodeNotFound()


def _get_errata_data(self, host, auth, uuid):
    """Get the errata here, while it's hot."""

    url = '{host}/katello/api/v2/systems/{id}/errata'.format(host=host,
                                                             id=uuid)
    r = requests.get(url, auth=auth, verify=VERIFY_SSL)
    r.raise_for_status()  # Raise an error if the request failed
    errata = r.json()['contexts']
    if not errata:
        raise NoErrataError()
    data = [ErrataItem(x['title'], x['type'], x['id'], x['issued'])
            for x in errata]
    return data


class DetailOverviewTab(nodes_tabs.DetailOverviewTab):
    template_name = 'infrastructure/nodes/_detail_overview_sat.html'

    def get_context_data(self, request, **kwargs):
        context = super(DetailOverviewTab,
                        self).get_context_data(request, **kwargs)
        if context['node'].uuid is None:
            return context

        # TODO(rdopiera) We can probably get the stack from the context.
        stack = _get_stack(request)
        if stack is None:
            return context

        try:
            host, auth, organization = _get_satellite_config(stack.parameters)
        except NoConfigError as e:
            horizon.messages.error(request, _(
                "No Satellite configuration found. "
                "Missing parameter %r."
            ) % e.param)
            return context
        except BadAuthError as e:
            horizon.messages.error(request, _(
                "Satellite configuration error, "
                "unknown authentication method %r."
            ) % e.auth)
            return context

        addresses = context['node'].addresses
        try:
            uuid = _find_uuid_by_mac(host, auth, organization, addresses)
        except NodeNotFound:
            return context

        # TODO(rdopiera) Should probably catch that requests exception here.
        try:
            data = self._get_errata_data(host, auth, uuid)
        except NoErrataError:
            return context
        context['errata'] = tables.ErrataTable(request, data=data)
        return context


class NodeDetailTabs(tabs.TabGroup):
    slug = "node_details"
    tabs = (DetailOverviewTab,)
