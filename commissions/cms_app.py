from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _

class CommissionsAppHook(CMSApp):
    name = _("Commissions")
    urls = ["commissions.urls"]

apphook_pool.register(CommissionsAppHook)