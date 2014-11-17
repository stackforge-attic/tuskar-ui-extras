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

import django.utils.text

from tuskar_ui import api
from tuskar_ui.infrastructure.overview import views
from tuskar_boxes.overview import forms


NODE_STATE_ICON = {
    api.node.DISCOVERING_STATE: 'fa-search',
    api.node.DISCOVERED_STATE: 'fa-search-plus',
    api.node.DISCOVERY_FAILED_STATE: 'fa-search-minus',
    api.node.MAINTENANCE_STATE: 'fa-exclamation-triangle',
    api.node.FREE_STATE: 'fa-minus',
    api.node.PROVISIONING_STATE: 'fa-spinner fa-spin',
    api.node.PROVISIONED_STATE: 'fa-check',
    api.node.DELETING_STATE: 'fa-spinner fa-spin',
    api.node.PROVISIONING_FAILED_STATE: 'fa-exclamation-circle',
    None: 'fa-question',
}


def flavor_nodes(request, flavor):
    """Lists all nodes that match the given flavor exactly."""
    for node in api.node.Node.list(request, maintenance=False):
        if all([
            int(node.cpus) == int(flavor.vcpus),
            int(node.memory_mb) == int(flavor.ram),
            int(node.local_gb) == int(flavor.disk),
            node.cpu_arch == flavor.cpu_arch,
        ]):
            yield node


def node_role(request, node):
    try:
        resource = api.heat.Resource.get_by_node(request, node)
    except LookupError:
        return None
    return resource.role


class IndexView(views.IndexView):
    template_name = "tuskar_boxes/overview/index.html"
    form_class = forms.EditPlan

    def get_context_data(self, *args, **kwargs):
        context = super(IndexView, self).get_context_data(*args, **kwargs)
        flavors = api.flavor.Flavor.list(self.request)
        flavors.sort(key=lambda np: (np.vcpus, np.ram, np.disk))
        for role in context['roles']:
            flavor =  role['role'].flavor(context['plan'])
            role['flavor_name'] = flavor.name if flavor else ''
        if not context['stack']:
            context['flavors'] = []
            for flavor in flavors:
                nodes = [{
                    'role': '',
                } for node in flavor_nodes(self.request, flavor)]
                roles = [role for role in context['roles']
                         if role['flavor_name'] == flavor.name]
                flavor = {
                    'name': flavor.name,
                    'vcpus': flavor.vcpus,
                    'ram': flavor.ram,
                    'disk': flavor.disk,
                    'cpu_arch': flavor.cpu_arch,
                    'nodes': nodes,
                    'roles': roles,
                }
                if nodes or roles:  # Don't list empty flavors
                    context['flavors'].append(flavor)
                context['free_roles'] = [role for role in context['roles']
                                         if not role['flavor_name']]
            for role in context['roles']:
                role['flavor_field'] = context['form'][role['id'] + '-flavor']
        else:
            nodes = []
            for node in api.node.Node.list(self.request, maintenance=False):
                role = node_role(self.request, node)
                nodes.append({
                    'uuid': node.uuid,
                    'role_name': role.name if role else '',
                    'role_slug': django.utils.text.slugify(role.name)
                        if role else '',
                    'state': node.state,
                    'state_slug': django.utils.text.slugify(
                        unicode(node.state)),
                    'state_icon': NODE_STATE_ICON.get(node.state,
                                                      NODE_STATE_ICON[None]),
                })
            context['nodes'] = nodes
        return context

    def get_progress_update(self, request, data):
        out = super(IndexView, self).get_progress_update(request, data)
        out['nodes'] = data.get('nodes', [])
        return out
