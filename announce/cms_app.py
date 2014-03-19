from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _

class AnnounceAppHook(CMSApp):
    name = _("Announce")
    urls = ["announce.urls"]

apphook_pool.register(AnnounceAppHook)