import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS
from django.db.models import Count
from django.db.models.deletion import Collector

from accounts.models import RhizomeUser, UserRating


class Command(BaseCommand):
    '''
    this should be run once
    '''
    
    def handle(*args, **options):
        # innactive (or haven't logged in recently) users with no important associated content?
        
        delta = datetime.timedelta(days=365)
        
        # these properties can't be filtered in query since names aren't valid
        q = RhizomeUser.objects.annotate(num_artworks=Count('artist/user'),
                                         num_exhibitions=Count('user/curator'),
                                         num_proposals=Count('user who created the proposal'),
                                         num_orgsubs=Count('the org sub admin')
        ).filter(num_artworks=0, num_exhibitions=0, num_proposals=0, num_orgsubs=0)
        
        q = q.filter(comment_comments__isnull=True, event__isnull=True,\
                     opportunity__isnull=True, post__isnull=True,\
                     approvalvote__isnull=True,\
                     newdonation__isnull=True, reblogpost__isnull=True,\
                     staffmember__isnull=True, downloadofthemonth__isnull=True,\
                     job__isnull=True, collectioncurator__isnull=True, rankvote__isnull=True)

        innactive_users = q.filter(is_active=False)
        dead_users = q.filter(last_login__lte=datetime.datetime.today() - delta, is_active=True)

        print 'deleting %s users...' % (innactive_users.count() + dead_users.count())

        innactive_users.delete()
        dead_users.delete()

        print 'done.'

        
