from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _

class ProgramsAppHook(CMSApp):
    name = _("Programs")
    urls = ["programs.urls"]

apphook_pool.register(ProgramsAppHook)