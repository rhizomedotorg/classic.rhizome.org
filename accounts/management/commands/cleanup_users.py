import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db.models.deletion import Collector
from django.db import router

from accounts.models import RhizomeUser


def get_related(queryset):
    using = router.db_for_read(queryset.model)
    coll = Collector(using=using)
    coll.collect(queryset)
    return coll.data

class Command(BaseCommand):
    '''
    '''
    
    def handle(*args, **options):
        # innactive (or haven't logged in recently) users with no important associated content?
        
        delta = datetime.timedelta(days=1000)
        innactive_users = RhizomeUser.objects.filter(is_active=False)
        dead_users = RhizomeUser.objects.filter(last_login__lte=datetime.datetime.today() - delta, is_active=True)

        for user in innactive_users:
            import pdb; pdb.set_trace()

            

