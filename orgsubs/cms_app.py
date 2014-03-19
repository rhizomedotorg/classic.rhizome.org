from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _

class OrgSubsAppHook(CMSApp):
    name = _("OrgSubs")
    urls = ["orgsubs.urls"]

apphook_pool.register(OrgSubsAppHook)