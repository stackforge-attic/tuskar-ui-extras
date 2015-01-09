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

from django.core import urlresolvers
import mock
from tuskar_ui import api
from tuskar_ui.infrastructure.overview import tests
from tuskar_ui.test import helpers


INDEX_URL = urlresolvers.reverse(
    'horizon:infrastructure:overview:index')


class BoxesViewsTests(helpers.BaseAdminViewTests):
    def test_index_edit_get(self):
        with (
            tests._mock_plan()
        ), (
            mock.patch('tuskar_ui.api.heat.Stack.list', return_value=[])
        ), (
            mock.patch('tuskar_ui.api.node.Node.list', return_value=[])
        ), (
            mock.patch('tuskar_ui.api.flavor.Flavor.list', return_value=[])
        ):
            res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(
            res, 'tuskar_boxes/overview/index.html')
        self.assertTemplateUsed(
            res, 'tuskar_boxes/overview/role_nodes_edit.html')

    def test_index_edit_post(self):
        roles = [api.tuskar.Role(role)
                 for role in self.tuskarclient_roles.list()]
        with (
            tests._mock_plan()
        ) as plan, (
            mock.patch('tuskar_ui.api.heat.Stack.list', return_value=[])
        ), (
            mock.patch('tuskar_ui.api.node.Node.list', return_value=[])
        ), (
            mock.patch('tuskar_ui.api.flavor.Flavor.list', return_value=[])
        ):
            plan.role_list = roles
            data = {
                'role-1-count': 1,
                'role-1-flavor': 'baremetal',
                'role-2-count': 0,
                'role-2-flavor': 'baremetal',
                'role-3-count': 0,
                'role-3-flavor': 'baremetal',
                'role-4-count': 0,
                'role-4-flavor': 'baremetal',
            }
            res = self.client.post(INDEX_URL, data)
            self.assertNoFormErrors(res)
            self.assertRedirectsNoFollow(res, INDEX_URL)
            api.tuskar.Plan.patch.assert_called_with(mock.ANY, plan.id, {
                'Object Storage-1::Flavor': u'baremetal',
                'Compute-1::Flavor': u'baremetal',
                'Controller-1::Flavor': u'baremetal',
                'Block Storage-1::Flavor': u'baremetal',
            })

    def test_index_live_get(self):
        stack = api.heat.Stack(tests.TEST_DATA.heatclient_stacks.first())
        stack.is_initialized = True
        stack.is_deployed = True
        roles = [api.tuskar.Role(role)
                 for role in self.tuskarclient_roles.list()]

        with (
            tests._mock_plan(**{
                'get_role_by_name.side_effect': None,
                'get_role_by_name.return_value': roles[0],
            })
        ), (
            mock.patch('tuskar_ui.api.heat.Stack.get_by_plan',
                       return_value=stack)
        ), (
            mock.patch('tuskar_ui.api.heat.Stack.events', return_value=[])
        ):
            res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(
            res, 'tuskar_boxes/overview/index.html')
        self.assertTemplateUsed(
            res, 'infrastructure/overview/deployment_live.html')
        self.assertTemplateUsed(
            res, 'tuskar_boxes/overview/role_nodes_live.html')

    def test_index_progress_get(self):
        stack = api.heat.Stack(tests.TEST_DATA.heatclient_stacks.first())

        with (
            tests._mock_plan()
        ), (
            mock.patch('tuskar_ui.api.heat.Stack.get_by_plan',
                       return_value=stack)
        ), (
            mock.patch('tuskar_ui.api.heat.Stack.is_deleting',
                       return_value=True)
        ), (
            mock.patch('tuskar_ui.api.heat.Stack.is_deployed',
                       return_value=False)
        ), (
            mock.patch('tuskar_ui.api.heat.Stack.resources',
                       return_value=[])
        ), (
            mock.patch('tuskar_ui.api.heat.Stack.events',
                       return_value=[])
        ):
            res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(
            res, 'tuskar_boxes/overview/index.html')
        self.assertTemplateUsed(
            res, 'infrastructure/overview/deployment_progress.html')
        self.assertTemplateUsed(
            res, 'tuskar_boxes/overview/role_nodes_status.html')
