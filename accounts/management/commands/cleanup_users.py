import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS
from django.db.models import Count
from django.db.models.deletion import Collector

from accounts.models import RhizomeUser, UserRating


class Command(BaseCommand):
    '''
    '''
    
    def handle(*args, **options):
        # innactive (or haven't logged in recently) users with no important associated content?
        
        delta = datetime.timedelta(days=1000)
        
        q = RhizomeUser.objects.annotate(num_artworks=Count('artist/user'),\
                                         num_exhibitions=Count('user/curator')\
        ).filter(num_artworks=0, num_exhibitions=0)
        
        import pdb; pdb.set_trace()

        q = q.filter(comment_comments__isnull=True, event__isnull=True,\
                     opportunity__isnull=True, post__isnull=True,\
                     member__isnull=True, approvalvote__isnull=True,\
                     newdonation__isnull=True, reblogpost__isnull=True,\
                     staffmember__isnull=True, downloadofthemonth__isnull=True,\
                     job__isnull=True, jobpostingpayment__isnull=True,\
                     collectioncurator__isnull=True, rankvote__isnull=True)

        innactive_users = q.filter(is_active=False)
        dead_users = q.filter(last_login__lte=datetime.datetime.today() - delta, is_active=True)

        users_to_delete = []

        for user in innactive_users:
            users_to_delete.append(user.id)

        for user in dead_users:
            users_to_delete.append(user.id)

        import pdb; pdb.set_trace()
        # bulk delete
        #RhizomeUser.objects.filter(id__in=users_to_delete).delete()

            

