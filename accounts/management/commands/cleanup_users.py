import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from accounts.models import RhizomeUser

from django.db.models.deletion import Collector
from django.contrib.admin.util import NestedObjects


WORTHY_RATING_CUTOFF = 20
LOGIN_CUTOFF_DAYS = 180
WORTHY_ARTWORK_STATUSES = ['approved', 'awaiting', 'to_consider', 'rejected']

def related_objs(q):
    collector = NestedObjects(using='default')
    collector.collect(q)
    return collector.data

class Command(BaseCommand):
    '''
    this should be run once,
    deletes innactive users who contribute nothing + spammers

      194845
    - 179224
    --------
       15621
    '''
    
    def handle(*args, **options):
        
        delta = datetime.timedelta(days=LOGIN_CUTOFF_DAYS)

        q = RhizomeUser.objects.filter(
            Q(artworks__isnull=True) | ~Q(artworks__status__in=WORTHY_ARTWORK_STATUSES),    # no worthy artworks
            Q(comment_comments__isnull=True) | ~Q(comment_comments__is_removed=False),      # no visible comments
            Q(user_rating__isnull=True) | Q(user_rating__rating__lte=WORTHY_RATING_CUTOFF), # has an unworthy low rating
            Q(post__isnull=True),                                                           # no blog posts
            Q(reblogpost__isnull=True),
            Q(rhiz_author__isnull=True),
            Q(newdonation__isnull=True),                                                    # no donations
            Q(downloadofthemonth__isnull=True),                                             # never authored a "download of the month"
            Q(prospective_user_admins__isnull=True),                                        # not an orgsub admin
            Q(user_membership__isnull=True) | \
            Q(user_membership__member_tools_exp_date__lte=datetime.datetime.now()),         # not currently a member
            Q(is_active=False) | \
            (Q(last_login__lte=datetime.datetime.today() - delta) & Q(is_active=True)),     # is innactive or hasn't logged in lately
            Q(proposals__isnull=True),                                                      # has never participated in commissions
            Q(rankvote__isnull=True),
            Q(approvalvote__isnull=True),
            Q(event__isnull=True) | ~Q(event__status__in=[1]) | ~Q(event__is_spam__in=[False]), # no visible announcements
            Q(opportunity__isnull=True) | ~Q(opportunity__status__in=[1]) | ~Q(opportunity__is_spam__in=[False]),
            Q(job__isnull=True) | ~Q(job__status__in=[1]) | ~Q(job__is_spam__in=[False]),
            Q(collectioncurator__isnull=True),                                              # never curated a collection
            Q(exhibitions__isnull=True) | ~Q(exhibitions__live=[True])                      # no visible exhibitions       
        )

        print 'deleting %s users...' % q.count()

        text_file = open('/tmp/output.txt', 'w')
        text_file.write('%s' % related_objs(q))
        # for o in q:
        #     try:
        #         text_file.write('%s' % related_objs(o))
        #     except:
        #         pass
            
        text_file.close()

        q.delete()

        print 'done.'
