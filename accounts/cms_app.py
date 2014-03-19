from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _

class AccountsAppHook(CMSApp):
    name = _("Accounts")
    urls = ["accounts.urls"]

apphook_pool.register(AccountsAppHook)