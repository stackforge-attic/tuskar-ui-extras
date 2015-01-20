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

from tuskar_ui.test import helpers

from tuskar_sat_ui.nodes import tabs


class SatTests(helpers.BaseAdminViewTests):
    def test_satellite_config(self):
        config = {
            tabs.SAT_CONFIG: {
                tabs.SAT_HOST_PARAM: 'http://example.com/',
                tabs.SAT_AUTH_PARAM: 'basic:user:pass',
                tabs.SAT_ORG_PARAM: 'ACME',
            },
        }

        with self.settings(**config):
            host_url, api_url, auth, org = tabs._get_satellite_config()
            self.assertEqual(host_url, 'http://example.com')
            self.assertEqual(api_url, 'http://example.com')
            self.assertEqual(auth, ('user', 'pass'))
            self.assertEqual(org, 'ACME')

    def test_satellite_config_different_api_url(self):
        config = {
            tabs.SAT_CONFIG: {
                tabs.SAT_HOST_PARAM: 'http://example.com/',
                tabs.SAT_API_PARAM: 'https://example.com/',
                tabs.SAT_AUTH_PARAM: 'basic:user:pass',
                tabs.SAT_ORG_PARAM: 'ACME',
            },
        }

        with self.settings(**config):
            host_url, api_url, auth, org = tabs._get_satellite_config()
            self.assertEqual(host_url, 'http://example.com')
            self.assertEqual(api_url, 'https://example.com')
            self.assertEqual(auth, ('user', 'pass'))
            self.assertEqual(org, 'ACME')

    def test_satellite_config_missing_all(self):
        config = {}

        with self.settings(**config):
            with self.assertRaises(tabs.NoConfigError) as e:
                host_url, api_url, auth, org = tabs._get_satellite_config()
        self.assertEqual(e.exception.param, tabs.SAT_CONFIG)

    def test_satellite_config_missing_one(self):
        params = {
            tabs.SAT_HOST_PARAM: 'http://example.com/',
            tabs.SAT_AUTH_PARAM: 'basic:user:pass',
            tabs.SAT_ORG_PARAM: 'ACME',
        }

        for param in [
            tabs.SAT_HOST_PARAM,
            tabs.SAT_AUTH_PARAM,
            tabs.SAT_ORG_PARAM,
        ]:
            broken_config = {
                tabs.SAT_CONFIG: dict(kv for kv in params.items()
                                      if kv[0] != param),
            }

            with self.settings(**broken_config):
                with self.assertRaises(tabs.NoConfigError) as e:
                    host_url, api_url, auth, org = tabs._get_satellite_config()
                self.assertEqual(e.exception.param, param)

    def test_satellite_config_unknown_auth(self):
        config = {
            tabs.SAT_CONFIG: {
                tabs.SAT_HOST_PARAM: 'http://example.com/',
                tabs.SAT_AUTH_PARAM: 'bad:user:pass',
                tabs.SAT_ORG_PARAM: 'ACME',
            },
        }

        with self.settings(**config):
            with self.assertRaises(tabs.BadAuthError) as e:
                host_url, api_url, auth, org = tabs._get_satellite_config()
            self.assertEqual(e.exception.auth, 'bad')

    def test_satellite_config_malformed_auth(self):
        config = {
            tabs.SAT_CONFIG: {
                tabs.SAT_HOST_PARAM: 'http://example.com/',
                tabs.SAT_AUTH_PARAM: 'bad',
                tabs.SAT_ORG_PARAM: 'ACME',
            },
        }

        with self.settings(**config):
            with self.assertRaises(tabs.BadAuthError) as e:
                api_url, api_url_url, auth, org = tabs._get_satellite_config()
            self.assertEqual(e.exception.auth, 'bad')
