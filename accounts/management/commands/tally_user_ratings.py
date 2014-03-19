from django.core.management.base import BaseCommand, CommandError
from accounts.models import RhizomeUser, UserRating,UserObjectPoints
from django.contrib.auth.models import User, UserManager
from threadedcomments.models import ThreadedComment
from announce.models import Event, Job, Opportunity
from blog.models import Post
from artbase.models import ArtworkStub, MemberExhibition
from resources.models import Festival, Program, Residency, Syllabus
import datetime
from itertools import chain
from operator import attrgetter, itemgetter


class Command(BaseCommand):
    """
    CRON JOB FOR 
        - ADDING RATINGS TO USERS
        - UPDATING POINTS TRACKING SYSTEM FOR OBJECTS/POINTS/USERS
    """

    def handle(self, *args, **options):
        users = RhizomeUser.objects.filter(is_active=True)
        five_years_ago = datetime.datetime.today() - datetime.timedelta(1800)
        
        for user in users:

            #### announcements worth 2 points
            valid_opps = Opportunity.objects.filter(user = user, status = 1,is_spam=False)
            valid_jobs = Job.objects.filter(user = user, status = 1,is_spam=False)
            valid_events = Event.objects.filter(user = user, status = 1,is_spam=False)                   


            #### spam -10 points
            invalid_opps = int(Opportunity.objects.filter(user = user, is_spam=True).count()*10)
            invalid_jobs = int(Job.objects.filter(user = user, is_spam=True).count()*10)
            invalid_events = int(Event.objects.filter(user = user, is_spam=True).count()*10)   

            #### resources worth 2 points
            festivals = Festival.objects.filter(user = user, visible = 1)
            programs = Program.objects.filter(user = user, visible = 1)
            residencies = Residency.objects.filter(user = user, visible = 1)
            syllabi = Syllabus.objects.filter(user = user, visible = 1)

            two_points = chain(valid_events, valid_opps, valid_jobs,festivals,programs,residencies,syllabi)
            
            for a in two_points:
                points_object,created = UserObjectPoints.objects.get_or_create(
                        user=user, 
                        content_type = a.content_type(), 
                        object_pk = a.id, 
                        points = 2
                )
                if created:
                    points_object.save()

                                        
            #### comments worth 2 points
            valid_comments = ThreadedComment.objects.filter(user = user, is_public = 1)
            for a in valid_comments:
                try:
                    points_object,created = UserObjectPoints.objects.get_or_create(
                            user=user, 
                            content_type = a.content_type, 
                            object_pk = a.id, 
                            points = 2
                    )
                    if created:
                        points_object.save()
                except:
                    pass
                
            #### blog posts = 5 points            
            blog_posts = Post.objects.filter(authors__id = user.id).filter(status = 2)
            for a in blog_posts:
                points_object,created = UserObjectPoints.objects.get_or_create(
                        user=user, 
                        content_type = a.content_type(), 
                        object_pk = a.id, 
                        points = 5
                    )
                if created:
                    points_object.save()            
                
                
            ##### artworks in artbase = 10 points
            artbase_artworks = ArtworkStub.objects.filter(user = user, status = "approved")
            for a in artbase_artworks:
                points_object,created = UserObjectPoints.objects.get_or_create(
                        user=user, 
                        content_type = a.content_type(), 
                        object_pk = a.id,
                        points=10
                    )
                if created:
                    points_object.save()    


            #### portfolio works worth 3 points
            portfolio_artworks = ArtworkStub.objects.filter(user = user).exclude(status = "unsubmitted").exclude(status="deleted") 
            
            #### member exhibitions = 3 points
            exhibitions = MemberExhibition.objects.filter(user = user, live = 1)
            
            exhibitions_and_portfolios = chain(exhibitions, portfolio_artworks)
            for a in exhibitions_and_portfolios:
                points_object,created = UserObjectPoints.objects.get_or_create(
                        user=user, 
                        content_type = a.content_type(), 
                        object_pk = a.id,
                        points=3
                )
                if created:
                    points_object.save()    
                
            #### add up the points
            points = sum([int(obj.points) for obj in UserObjectPoints.objects.filter(user=user)])
#             points = int(len(valid_comments)) + int(len(valid_opps)) + int(len(valid_jobs)) + int(len(valid_events)) \
#                     + int(len(blog_posts)) + int(len(artbase_artworks)) + pint(len(ortfolio_artworks)) \
#                     + int(len(exhibitions)) + int(len(festivals)) + int(len(syllabi)) + int(len(programs)) + int(len    \                
#                     (residencies)) \
            
            negative_points = invalid_opps + invalid_jobs + invalid_events
            points = points - negative_points
            
            #old accounts get extra points
            if user.date_joined <= five_years_ago:
                points = points + 15
            
            #members get points
            if user.is_member():
                points = points + 15
                 
            try:
                rating = UserRating.objects.get(user=user)
            except:
                rating = UserRating(user=user)
            rating.rating = points
            rating.save()
            
            
            
            
            
            
            
            
            
            
            
            
