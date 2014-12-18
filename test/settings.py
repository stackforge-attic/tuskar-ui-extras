from openstack_dashboard.utils import settings
import test.enabled
from tuskar_ui.test.settings import *  # noqa


INSTALLED_APPS = list(INSTALLED_APPS)  # Make sure it's mutable
settings.update_dashboards([test.enabled], HORIZON_CONFIG, INSTALLED_APPS)
