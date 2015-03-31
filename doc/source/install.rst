Production installation instructions
====================================

First install the ``tuskar-ui-extras`` package::

    yum install openstack-tuskar-ui-extras

Then add enabling files into /usr/share/openstack-dashboard/openstack_dashboard/enabled.

``_60_tuskar_boxes.py``::

    PANEL = 'overview'
    PANEL_DASHBOARD = 'infrastructure'
    ADD_PANEL = 'tuskar_boxes.overview.panel.Overview'
    ADD_INSTALLED_APPS = [
        'tuskar_boxes',
    ]

``_60_tuskar_sat_ui.py``::

    PANEL = 'nodes'
    PANEL_DASHBOARD = 'infrastructure'
    ADD_PANEL = 'tuskar_sat_ui.nodes.panel.Nodes'
    ADD_INSTALLED_APPS = [
        'tuskar_sat_ui',
    ]

Restart Horizon.


Development install instructions
================================

Go into your Horizon directory::

    cd horizon/

Install Tuskar UI Extras with all dependencies in your virtual environment::

    tools/with_venv.sh pip install -r ../tuskar-ui-extras/requirements.txt
    tools/with_venv.sh pip install -e ../tuskar-ui-extras/


Enabling Tuskar-UI Boxes
------------------------

To enable the Tuskar-UI Boxes plugin in Horizon, copy the config file::

    cp ../tuskar-ui-extras/_60_tuskar_boxes.py.example openstack_dashboard/local/enabled/_60_tuskar_boxes.py


Enabling Tuskar Satellite Integration
-------------------------------------

To enable the Tuskar-SAT6 UI plugin in Horizon, copy the config file::

    cp ../tuskar-ui-extras/_60_tuskar_sat_ui.py.example openstack_dashboard/local/enabled/_60_tuskar_sat_ui.py


Setting up the Satellite integration
====================================

You need to configure the connection to Satellite for the Satellite integration
to work. This is done by editing ``openstack_dashboard/local/settings.local.py``
and adding a parameter called SATELLITE_CONFIG, like this::

    SATELLITE_CONFIG = {
        'satellite_host': 'https://dhcp-8-29-162.lab.eng.rdu2.redhat.com',
        'satellite_api': 'http://dhcp-8-29-162.lab.eng.rdu2.redhat.com',
        'satellite_org': '1',
        'satellite_auth': 'basic:user:password',
    }

 * satellite_host: The URL to the Satellite server, f.ex 'https://example.com/'
 * satellite_api: The URL to the Satellite API. Optional. If it's the same as the
   satellite_host, you can skip this.
 * satellite_org: The numeric ID of the organization you want to use, typically '1'.
 * satellite_auth: A string containing authentication information.


Authentication information
--------------------------

The Satellite authentication information should be in the format
'protocol:authstring'. Currently two protocols are supported, ``basic`` and
``oauth``.

For basic authentication the authstring should be the username and password,
separated by a colon. This means you can't have a colon in the username.
For example::

    basic:username:password

For OAuth the authstring should be a client key and a client secret. These are
obtained from your OAuth system. For example::

    oauth:client:7TgjxHen20ghdfo739bhGDlncHN7Ft5E

