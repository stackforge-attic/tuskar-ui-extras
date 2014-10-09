Installation instructions
=========================

Tuskar-UI Boxes
---------------

Go into your Horizon diroectory::

    cd horizon/

Install Tuskar UI Extras with all dependencies in your virtual environment::

    tools/with_venv.sh pip install -r ../tuskar-ui-extras/requirements.txt
    tools/with_venv.sh pip install -e ../tuskar-ui-extras/

And enable the Tuskar-UI Boxes plugin in Horizon::

    cp ../tuskar-ui-extras/_60_tuskar_boxes.py.example openstack_dashboard/local/enabled/_60_tuskar_boxes.py
