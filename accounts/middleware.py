# based on https://gist.github.com/ericflo/268379

from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import User
 

ONLINE_THRESHOLD = getattr(settings, 'ONLINE_THRESHOLD', 60 * 12)


def get_online_now(self):
    return User.objects.filter(id__in=self.online_now_ids or [])

class OnlineNowMiddleware(object):
    # Maintains a list of users who have interacted with the website recently.
 
    def process_request(self, request):
        uids = cache.get('online-now', [])
        
        # lookup individual online uid keys
        online_keys = ['online-%s' % u for u in uids]
        fresh = cache.get_many(online_keys).keys()
        online_now_ids = [int(k.replace('online-', '')) for k in fresh]
        
        # if user authenticated, add their id to the list
        if request.user.is_authenticated():
            uid = request.user.id
            if uid not in online_now_ids:
                online_now_ids.append(uid)
            cache.set('online-%s' % (request.user.pk,), True, ONLINE_THRESHOLD)

        # sexy monkey patching
        request.__class__.online_now_ids = online_now_ids
        request.__class__.online_now = property(get_online_now)

        cache.set('online-now', online_now_ids, ONLINE_THRESHOLD)