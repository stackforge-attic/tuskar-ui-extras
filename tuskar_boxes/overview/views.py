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

from tuskar_ui import api
from tuskar_ui.infrastructure.overview import views


def flavor_nodes(request, flavor):
    """Lists all nodes that match the given flavor exactly."""
    for node in api.node.Node.list(request):
        if all([
            int(node.cpus) == int(flavor.vcpus),
            int(node.memory_mb) == int(flavor.ram),
            int(node.local_gb) == int(flavor.disk),
            # TODO(rdopieralski) add architecture when available
        ]):
            yield node

class IndexView(views.IndexView):
    template_name = "tuskar_boxes/overview/index.html"

    def get_context_data(self, *args, **kwargs):
        context = super(IndexView, self).get_context_data(*args, **kwargs)
        flavors = api.flavor.Flavor.list(self.request)
        flavors.sort(key=lambda np: (np.vcpus, np.ram, np.disk))
        context['flavors'] = []
        for flavor in flavors:
            nodes = [{
                'role': '',
            } for node in flavor_nodes(self.request, flavor)]
            flavor = {
                'name': flavor.name,
                'vcpus': flavor.vcpus,
                'ram': flavor.ram,
                'disk': flavor.disk,
                'nodes': nodes,
            }
            if nodes:  # Don't list empty flavors
                context['flavors'].append(flavor)
        return context
