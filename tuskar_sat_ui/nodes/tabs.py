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
import requests
import urllib

from collections import namedtuple
from horizon import tabs
from tuskar_ui.infrastructure.nodes import tabs as nodes_tabs
from .tables import ErrataTable


ErrataItem = namedtuple('ErrataItem', ['title', 'type', 'id', 'issued'])


class DetailOverviewTab(nodes_tabs.DetailOverviewTab):
    template_name = 'infrastructure/nodes/_detail_overview_sat.html'

    def get_context_data(self, request):
        result = super(DetailOverviewTab, self).get_context_data(request)
        if result['node'].uuid is None:
            return result

        # Some currently hardcoded values:
        mac = '"52:54:00:4F:D8:65"'  # Hardcode for now
        host = 'http://sat-perf-04.idm.lab.bos.redhat.com'  # Hardcode for now
        auth = ('admin', 'changeme')

        # Get the errata here
        host = host.strip('/')  # Get rid of any trailing slash in the host url

        # Pick up the UUID from the MAC address This makes no sense, as we
        # need both MAC address and the interface, and we don't have the
        # interface, so we need to make multiple slow searches. If the
        # Satellite UUID isn't the same as this one, and it probably isn't we
        # need to store a mapping somewhere.
        url = '{host}/katello/api/v2/systems'.format(host=host)
        for interface in ['eth0', 'eth1', 'en0', 'en1']:

            q = 'facts.net.interface.{iface}.mac_address:{mac}'.format(
                iface=interface, mac=mac)
            r = requests.get(url, params={'search': q}, auth=auth)
            results = r.json()['results']
            if results:
                break
        else:
            # No node found
            result['errata'] = None
            return result

        uuid = results[0]['uuid']
        errata_url = '{host}/katello/api/v2/systems/{id}/errata'
        r = requests.get(errata_url.format(host=host, id=uuid), auth=auth)
        errata = r.json()['results']
        if not errata:
            result['errata'] = None
        else:
            data = [ErrataItem(x['title'], x['type'], x['id'], x['issued'])
                    for x in errata]
            result['errata'] = ErrataTable(request, data=data)
        return result


class NodeDetailTabs(tabs.TabGroup):
    slug = "node_details"
    tabs = (DetailOverviewTab,)
