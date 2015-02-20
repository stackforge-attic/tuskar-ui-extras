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

from django.conf import urls
from tuskar_ui.infrastructure.nodes import urls as tuskar_urls

from tuskar_sat_ui.nodes import views as sat_views


urlpatterns = [url for url in tuskar_urls.urlpatterns if url.name != 'detail']
urlpatterns.extend(urls.patterns(
    urls.url(r'^(?P<node_uuid>[^/]+)/$', sat_views.DetailView.as_view(),
             name='detail'),
))
