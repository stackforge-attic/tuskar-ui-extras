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


SAT_HOST_PARAM = 'satellite_host'
SAT_API_PARAM = 'satellite_api'
SAT_AUTH_PARAM = 'satellite_auth'
SAT_ORG_PARAM = 'satellite_org'
SAT_CONFIG = 'SATELLITE_CONFIG'

VERIFY_SSL = not getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
LOG = logging.getLogger('tuskar_sat_ui')
ErrataItem = collections.namedtuple('ErrataItem', [
    'title',
    'type',
    'id',
    'host_id',
    'issued',
    'admin_url',
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


def _get_satellite_config():
    """Find the Satellite configuration data.

    The configuration data is store in Heat as parameters.  They may be
    stored directly as Heat parameters, or in a the JSON structure stored
    in ExtraConfig.
    """

    try:
        config = getattr(settings, SAT_CONFIG)
    except AttributeError:
        raise NoConfigError(SAT_CONFIG, 'Parameter %r missing.' % SAT_CONFIG)

    for param in [SAT_HOST_PARAM, SAT_AUTH_PARAM, SAT_ORG_PARAM]:
        if param not in config:
            raise NoConfigError(param, 'Parameter %r missing.' % param)

    admin_url = config[SAT_HOST_PARAM]
    # Get rid of any trailing slash in the admin url
    admin_url = admin_url.strip('/')

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

    if SAT_API_PARAM in config:
        api_url = config[SAT_API_PARAM]
        # Get rid of any trailing slash in the API url
        api_url = api_url.strip('/')
    else:
        api_url = admin_url

    return admin_url, api_url, auth, organization


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


def _find_uuid_by_mac(api_url, auth, organization, addresses):
    """Pick up the UUID from the MAC address.

    This makes no sense, as we need both MAC address and the interface, and
    we don't have the interface, so we need to make multiple slow searches.
    If the Satellite UUID isn't the same as this one, and it probably
    isn't, we need to store a mapping somewhere.
    """

    url = '{api_url}/katello/api/v2/systems'.format(api_url=api_url)
    for mac in addresses:
        for interface in ['eth0', 'eth1', 'en0', 'en1']:
            q = 'facts.net.interface.{iface}.mac_address:"{mac}"'.format(
                iface=interface, mac=mac.upper())
            params = {'search': q, 'organization_id': organization}
            r = requests.get(url, params=params, auth=auth,
                             verify=VERIFY_SSL)
            r.raise_for_status()  # Raise an error if the request failed
            contexts = r.json()['results']
            if contexts:
                return contexts[0]['uuid']
    raise NodeNotFound()


def _get_errata_data(admin_url, api_url, auth, uuid):
    """Get the errata here, while it's hot."""

    url = '{url}/katello/api/v2/systems/{id}/errata'.format(url=api_url,
                                                            id=uuid)
    r = requests.get(url, auth=auth, verify=VERIFY_SSL)
    r.raise_for_status()  # Raise an error if the request failed
    errata = r.json()['results']
    if not errata:
        raise NoErrataError()
    data = [ErrataItem(x['title'], x['type'], x['errata_id'], uuid,
            x['issued'], admin_url) for x in errata]
    return data


class DetailOverviewTab(nodes_tabs.DetailOverviewTab):
    template_name = 'infrastructure/nodes/_detail_overview_sat.html'

    def get_context_data(self, request, **kwargs):
        context = super(DetailOverviewTab,
                        self).get_context_data(request, **kwargs)
        if context['node'].uuid is None:
            return context

        try:
            admin_url, api_url, auth, organization = _get_satellite_config()
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
            uuid = _find_uuid_by_mac(api_url, auth, organization, addresses)
        except NodeNotFound:
            return context

        # TODO(rdopiera) Should probably catch that requests exception here.
        try:
            data = _get_errata_data(admin_url, api_url, auth, uuid)
        except NoErrataError:
            return context
        context['errata'] = tables.ErrataTable(request, data=data)
        return context


class NodeDetailTabs(tabs.TabGroup):
    slug = "node_details"
    tabs = (DetailOverviewTab,)
