from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _

class MailingListsAppHook(CMSApp):
    name = _("MailingLists")
    urls = ["mailinglists.urls"]

apphook_pool.register(MailingListsAppHook)