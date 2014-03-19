from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _

class ArtBaseAppHook(CMSApp):
    name = _("ArtBase")
    urls = ["artbase.urls"]

apphook_pool.register(ArtBaseAppHook)