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
import operator

from django.core.urlresolvers import reverse
import django.utils.text
from django.utils.translation import ugettext_lazy as _
import horizon.forms
from openstack_dashboard.api import base as api_base

from tuskar_ui import api
from tuskar_ui.infrastructure.flavors import utils
from tuskar_ui.infrastructure.overview import views
from tuskar_ui.utils import metering

from tuskar_boxes.overview import forms


MATCHING_DEPLOYMENT_MODE = utils.matching_deployment_mode()
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


def flavor_nodes(request, flavor, exact_match=True):
    """Lists all nodes that match the given flavor.

       If exact_match is True, only nodes that match exactly will be listed.
       Otherwise, all nodes that have at least the required resources will
       be listed.
    """
    if exact_match:
        matches = operator.eq
    else:
        matches = operator.ge
    for node in api.node.Node.list(request, maintenance=False):
        if all(matches(*pair) for pair in (
            (int(node.cpus or 0), int(flavor.vcpus or 0)),
            (int(node.memory_mb or 0), int(flavor.ram or 0)),
            (int(node.local_gb or 0), int(flavor.disk or 0)),
            (node.cpu_arch, flavor.cpu_arch),
        )):
            yield node


def node_role(request, node):
    try:
        resource = api.heat.Resource.get_by_node(request, node)
    except LookupError:
        return None
    return resource.role


def _node_data(request, nodes):
    for node in nodes:
        role = node_role(request, node)
        yield {
            'uuid': node.uuid,
            'role_name': role.name if role else '',
            'role_slug': django.utils.text.slugify(role.name) if role else '',
            'node_title': unicode(_("{0} node").format(role.name.title())
                                  if role else _("Free node")),
            'state': node.state,
            'state_slug': django.utils.text.slugify(unicode(node.state)),
            'state_icon': NODE_STATE_ICON.get(node.state,
                                              NODE_STATE_ICON[None]),
            'cpu_arch': node.cpu_arch,
            'cpus': node.cpus,
            'memory_mb': node.memory_mb,
            'local_gb': node.local_gb,
        }


def _flavor_data(request, flavors, flavor_roles):
    for flavor in flavors:
        nodes = list(_node_data(request,
                                flavor_nodes(request, flavor,
                                             MATCHING_DEPLOYMENT_MODE)))
        roles = flavor_roles.get(flavor.name, [])
        if nodes or roles:
            # Don't list empty flavors
            yield {
                'name': flavor.name,
                'vcpus': flavor.vcpus,
                'ram': flavor.ram,
                'disk': flavor.disk,
                'cpu_arch': flavor.cpu_arch,
                'nodes': nodes,
                'roles': roles,
            }


class IndexView(views.IndexView):
    template_name = "tuskar_boxes/overview/index.html"
    form_class = forms.EditPlan

    def get_data(self, request, context, *args, **kwargs):
        data = super(IndexView, self).get_data(request, context,
                                               *args, **kwargs)
        nodes = list(_node_data(
            request, api.node.Node.list(request, maintenance=False),
        ))
        nodes.sort(key=lambda node: node.get('role_name'))
        nodes.reverse()
        data['nodes'] = nodes

        if not data['stack']:
            flavors = api.flavor.Flavor.list(self.request)
            if not MATCHING_DEPLOYMENT_MODE:
                # In the POC mode, only one flavor is allowed.
                flavors = flavors[:1]
            flavors.sort(key=lambda np: (np.vcpus, np.ram, np.disk))

            roles = data['roles']
            free_roles = []
            flavor_roles = {}
            for role in roles:
                if 'form' in data:
                    role['flavor_field'] = data['form'][role['id'] + '-flavor']
                flavor = role['role'].flavor(data['plan'])
                if flavor and flavor.name in [f.name for f in flavors]:
                    role['flavor_name'] = flavor.name
                    flavor_roles.setdefault(flavor.name, []).append(role)
                else:
                    role['flavor_name'] = ''
                    field = role.get('flavor_field')
                    if field:
                        field.initial = 0
                    free_roles.append(role)
                role['is_valid'] = role[
                    'role'].is_valid_for_deployment(data['plan'])
            data['free_roles'] = free_roles
            flavor_data = list(
                _flavor_data(self.request, flavors, flavor_roles))
            data['flavors'] = flavor_data
            data['no_flavor_nodes'] = [
                node for node in nodes
                if not any(node in d['nodes'] for d in flavor_data)
            ]
        else:
            distribution = collections.Counter()

            for node in nodes:
                distribution[node['role_name']] += 1
            for role in data['roles']:
                if nodes:
                    role['distribution'] = int(
                        float(distribution[role['name']]) / len(nodes) * 100)
                else:
                    role['distribution'] = 0

            if api_base.is_service_enabled(request, 'metering'):
                for role in data['roles']:
                    role['graph_url'] = (
                        reverse('horizon:infrastructure:roles:performance',
                                args=[role['id']]) + '?' +
                        metering.url_part('hardware.cpu.load.1min', False) +
                        '&date_options=0.041666'
                    )
        return data

    def get_progress_update(self, request, data):
        out = super(IndexView, self).get_progress_update(request, data)
        out['nodes'] = data.get('nodes', [])
        return out

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['header_actions'] = [{
            'name': _('Edit Global Configuration'),
            'show_name': True,
            'url': reverse('horizon:infrastructure:overview:config'),
            'icon': 'fa-pencil',
            'ajax_modal': True,
        }, {
            'name': _('Register Nodes'),
            'show_name': True,
            'url': reverse('horizon:infrastructure:nodes:register'),
            'icon': 'fa-plus',
            'ajax_modal': True,
        }]
        return context


class GlobalServiceConfigView(horizon.forms.ModalFormView):
    form_class = forms.GlobalServiceConfig
    template_name = "tuskar_boxes/overview/global_service_config.html"
    submit_label = _("Save Configuration")

    def get_success_url(self):
        return reverse('horizon:infrastructure:overview:index')
