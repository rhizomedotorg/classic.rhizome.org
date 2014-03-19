from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _

class BlogAppHook(CMSApp):
    name = _("Blog")
    urls = ["blog.urls"]

apphook_pool.register(BlogAppHook)
