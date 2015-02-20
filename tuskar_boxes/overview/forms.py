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

import logging

import django.forms
from django.utils.translation import ugettext_lazy as _
import horizon.exceptions
from tuskar_ui import api
from tuskar_ui.infrastructure.overview import forms
from tuskar_ui.infrastructure.parameters import forms as parameters_forms

LOG = logging.getLogger(__name__)


class EditPlan(forms.EditPlan):
    def __init__(self, *args, **kwargs):
        super(EditPlan, self).__init__(*args, **kwargs)
        self.fields.update(self._role_flavor_fields(self.plan))

    def _role_flavor_fields(self, plan):
        fields = {}
        for role in plan.role_list:
            field = django.forms.CharField(
                label=_("Flavor for {0}").format(role.name),
                initial=role.flavor(plan).name if role.flavor(plan) else '',
                required=False,
                widget=django.forms.HiddenInput(attrs={
                    'class': "boxes-flavor",
                }),
            )
            field.role = role
            fields['%s-flavor' % role.id] = field
        return fields

    def handle(self, request, data):
        result = super(EditPlan, self).handle(request, data)
        parameters = dict(
            (field.role.flavor_parameter_name, data[name])
            for (name, field) in self.fields.items()
            if name.endswith('-flavor')
        )
        try:
            self.plan = self.plan.patch(request, self.plan.uuid, parameters)
        except Exception as e:
            horizon.exceptions.handle(request, _("Unable to update the plan."))
            LOG.exception(e)
            return False
        return result

    def clean(self):
        cleaned_data = super(EditPlan, self).clean()
        # If a role has no flavor, it should have no nodes.
        for key, value in cleaned_data.items():
            if key.endswith('-flavor'):
                if not value:
                    cleaned_data[key.replace('-flavor', '-count')] = 0
        return cleaned_data


class GlobalServiceConfig(horizon.forms.SelfHandlingForm):
    def __init__(self, *args, **kwargs):
        super(GlobalServiceConfig, self).__init__(*args, **kwargs)
        self.fields.update({
            k: v for (k, v) in
            parameters_forms.parameter_fields(self.request).iteritems()
            if '::' not in k
        })

    def handle(self, request, data):
        plan = api.tuskar.Plan.get_the_plan(self.request)

        try:
            plan.patch(request, plan.uuid, data)
        except Exception as e:
            horizon.exceptions.handle(
                request,
                _("Unable to update the service configuration."))
            LOG.exception(e)
            return False
        else:
            horizon.messages.success(
                request,
                _("Service configuration updated."))
            return True
