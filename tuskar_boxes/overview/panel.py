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

from django.utils.translation import ugettext_lazy as _
import horizon
import tuskar_ui.infrastructure.dashboard as tuskar_dashboard
from tuskar_ui.infrastructure.overview import panel


class Overview(horizon.Panel):
    name = _("Overview")
    slug = "overview"


tuskar_dashboard.Infrastructure.unregister(panel.Overview)
tuskar_dashboard.Infrastructure.register(Overview)
