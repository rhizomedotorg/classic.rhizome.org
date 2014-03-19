import calendar
import datetime
import os

from calendar import HTMLCalendar
from datetime import date
from itertools import groupby, chain
from math import floor
from operator import attrgetter

import django.dispatch

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage, send_mail
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _

from accounts.models import ActivityStream
from bbcode.fields import BBCodeCharField,BBCodeTextField
from countries.models import Country, UsState
from mailinglists.models import MLMessage
from utils.helpers import strip_bbcode

from moderation.utils import ModelModerator, moderator
from moderation.anti_spam import check_post_for_spam_via_defensio

from mailinglists.signals import send_to_announce_mailing_list


EVENT_SUB_TYPES = (
    ('Conference','Conference'), 
    ('Exhibition', 'Exhibition'), 
    ('Festival','Festival'), 
    ('Talk/Lecture','Talk/Lecture'), 
    ('Online Broadcast', 'Online Broadcast'), 
    ('Panel','Panel'), 
    ('Performance','Performance'), 
    ('Project Launch','Project Launch'), 
    ('Screening','Screening'), 
    ('Symposium','Symposium'), 
    ('Workshop','Workshop'),
    ('Other', 'Other')
    )
    
OPPORTUNITY_SUB_TYPES = (
    ('Academic Programs','Academic Programs'),
    ('Call for Artists', 'Call for Artists'), 
    ('Call for Curators','Call for Curators'), 
    ('Call for Artworks','Call for Artworks'), 
    ('Call for Papers','Call for Papers'), 
    ('Call for Participation','Call for Participation'),
    ('Call for Proposals','Call for Proposals'), 
    ('Call for Submissions','Call for Submissions'),
    ('Fellowships','Fellowships'),
    ('Funding','Funding'),
    ('Residencies','Residencies'),
    ('Other', 'Other')
    )

JOB_SUB_TYPES = (
    ('Academic','Academic'),
    ('Arts','Arts'),
    ('Artist Assistance', 'Artist Assistance'),
    ('Commercial','Commercial'),
    ('Internship','Internship'),
    ('Non-Profit','Non-Profit'),
    ('Technology','Technology'),
    ('Other', 'Other')
    )

def get_opp_upload_to(self, filename):
    return 'announce/images/opportunities/%s' % (filename.replace(" ", "-"))

def get_job_upload_to(self, filename):
    return 'announce/images/jobs/%s' % (filename.replace(" ", "-"))
    
def get_event_upload_to(self, filename):
    return 'announce/images/events/%s' % (filename.replace(" ", "-"))

def get_thumb_upload_to(self, filename):
    return '%s' % filename.replace(" ", "-")


class AnnounceModel(models.Model):
    """
    Abstract base model for all announcements. 
    """
    created = models.DateTimeField(null=False, editable=False)
    modified = models.DateTimeField(null=False, editable=False, auto_now=True)
    title = BBCodeCharField(null=False, max_length=255)
    description = BBCodeTextField(null=False)
    user = models.ForeignKey(User, null=False)
    username = models.CharField(max_length=30,  editable=False, db_index = True)
    url = models.URLField(null=False)
    ip_address = models.IPAddressField(null=True, blank=True)
    status = models.BooleanField(default = False, db_index = True)
    allow_comments = models.BooleanField(_('allow comments'), default=True)
    is_spam = models.BooleanField(default = False, db_index = True)
    image = models.ImageField(upload_to = get_job_upload_to,null=True, blank=True)
    thumbnail =  models.ImageField(upload_to = get_thumb_upload_to,null=True, blank=True)#created in view from image

    venue_name = models.CharField(max_length=100, null=True, blank=True)
    venue_address = models.CharField(max_length=100, null=True, blank=True)

    city = models.CharField(max_length=75, null=True, blank=True)
    state = models.ForeignKey(UsState, to_field='name',null=True,blank=True)
    country = models.ForeignKey(Country,null=True,blank=True) 
    locality_province = models.CharField(max_length=100, null=True, blank=True)
    zip_postal_code = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        abstract = True

    def save(self):
        if not self.id:
            self.created = datetime.datetime.now()
        if not self.created:
            self.created = datetime.datetime.now()

        ''' On save, strip html and update timestamps '''
        self.title = strip_tags(self.title)
        self.url = strip_tags(self.url)
        self.description = strip_tags(self.description)
        super(AnnounceModel, self).save()

    def can_edit(self):
        pass

    def content_type_id(self):
        ct = ContentType.objects.get_for_model(self)
        return ct.id
    
    def content_type(self):
        ct = ContentType.objects.get_for_model(self)
        return ct

    def create_description(self):
        if self.description:
            stripped_body = strip_bbcode(self.description)
            graphs = [graph for graph in stripped_body.split("\n")]
            for graph in  graphs:
                words = [word for word in graph.split(" ")]
                if len(words) > 20:
                    return graph.strip()
        return self.description

    def description_strip_bbcode(self):
        return strip_bbcode(self.description)
    
    def get_thumbnail(self):
        try:
            if os.path.exists(self.thumbnail.path):
                return self.thumbnail
            else:
                return None
        except:
            return None

    def has_been_sent_to_list(self):
        #for checking to see if sent to rhizome listservs, for now only checks for messages
        try:
            messages = MLMessage.objects.filter(content_type = self.content_type_id(), object_pk = self.id)
        except:
            messages = None
        
        if messages:
            sent = True
        else:
            sent = None
        return sent

    def get_location_details(self):
        location = ''
        if self.venue_name:
            location += '%s ' % self.venue_name
        if self.venue_address:
            location += '%s, ' % self.venue_address

        if self.city and self.state and self.zip_postal_code and self.locality_province:
            location += '%s, %s  %s %s' % (self.city, self.state, self.locality_province, self.zip_postal_code)
        
        if self.city and self.state and self.zip_postal_code and not self.locality_province:
            location += '%s, %s  %s' % (self.city, self.state, self.zip_postal_code)
        
        if self.city and self.state and not self.zip_postal_code and not self.locality_province:
            location += '%s, %s' % (self.city, self.state)        
        
        if self.city and not self.state and self.zip_postal_code and self.locality_province:
            location += '%s, %s %s' % (self.city, self.locality_province, self.zip_postal_code) 

        if self.city and not self.state and self.zip_postal_code and not self.locality_province:
            location += '%s, %s' % (self.city, self.zip_postal_code)                          
        
        if self.country:
            location += ', %s' % (self.country)  
   
        return location 

    def get_html_location(self):
        location = ''
        if self.venue_name:
            location += '%s <br />' % self.venue_name
        if self.venue_address:
            location += '%s <br />' % self.venue_address

        if self.city and self.state and self.zip_postal_code and self.locality_province:
            location += '%s, %s  %s %s <br />' % (self.city, self.state, self.locality_province, self.zip_postal_code)
        
        if self.city and self.state and self.zip_postal_code and not self.locality_province:
            location += '%s, %s  %s <br />' % (self.city, self.state, self.zip_postal_code)
        
        if self.city and self.state and not self.zip_postal_code and not self.locality_province:
            location += '%s, %s <br />' % (self.city, self.state)        
        
        if self.city and not self.state and self.zip_postal_code and self.locality_province:
            location += '%s, %s %s <br />' % (self.city, self.locality_province, self.zip_postal_code) 

        if self.city and not self.state and self.zip_postal_code and not self.locality_province:
            location += '%s, %s <br />' % (self.city, self.zip_postal_code)                          
        
        if self.country:
            location += '%s' % (self.country)  

        return location 

    def get_previous_post(self):
        return self.get_previous_by_publish(status__gte=1)

    def get_next_post(self):
        return self.get_next_by_publish(status__gte=1)

    def get_absolute_url(self):
        return "/announce/%s/%s/view/" % (self.type_for_url(), self.id)

    def edit_url(self):
        return "/announce/%s/%s/edit/" % (self.type_for_url(), self.id)

    def type_for_url(self):
        pass # override

    def __unicode__(self):
        return '%s by %s on %s' % (self.title, self.user, self.created)

class AnnounceModelModerator(ModelModerator):
    def requires_moderation(self, post):
        if isinstance(post, Job) and post.is_paid(): # paid jobs pass
            return False
        
        if post.user.get_profile().is_trusted():
            return False
        return True

    def auto_detect_spam(self, post):
        if check_post_for_spam_via_defensio(post.description):
            return (True, '')
        return (False, '')

    def moderation_queued(self, post):
        post.status = False

    def moderation_fail(self, post, request):
        post.status = False
        post.is_spam = True
        post.user.get_profile().is_active = False
        post.user.get_profile().save()

    def moderation_pass(self, post, request):
        post.status = True 
        post.is_spam = False 
        post.user.get_profile().add_points(3)
        send_to_announce_mailing_list(post.__class__, post, created=True)
        send_mail('Content Approved', self.approved_message_text(post), settings.DEFAULT_FROM_EMAIL, [post.user.email])

    def approved_message_text(self, post):
        return '%s, your announcement has been approved by our moderators.\n\nhttp://%s%s' % (
            post.user.get_profile(),
            Site.objects.get_current().domain,
            post.get_absolute_url()
        )

    def admin_info(self, post):
        return (
            ('author', '<a target="_blank" href="%s">%s</a>' % (post.user.get_absolute_url(), post.user)),
            ('title', post.title),
            ('submitted', post.created),
            ('type', post.content_type()),
            ('description', post.description),
        ) 

class Event(AnnounceModel):
    facebook_url = models.URLField(null=True, blank=True)
    type = models.CharField(max_length=50, default='event', editable=False,db_index = True)
    subtype = models.CharField(_('Type of Event'),max_length=50, choices=EVENT_SUB_TYPES, null=True, db_index = True)
    start_date = models.DateTimeField(null=False, db_index = True)
    end_date =  models.DateTimeField(null=False)

    def get_absolute_url(self):
        return "/announce/events/%s/view/" % (self.id)
    
    def edit_url(self):
        return "/announce/events/%s/edit/" % (self.id)
            
    def calendar_day(self):
        return self.start_date
        
    def type_for_url(self):
        return "events"

    def can_edit(self):
        now = datetime.datetime.now()
        if self.end_date > now:
            return True
        return False
        
    def save(self, *args, **kwargs):
        self.subtype = strip_tags(self.subtype)
        super(Event, self).save(*args, **kwargs)

class Opportunity(AnnounceModel):
    type = models.CharField(max_length=50, default='opportunity', editable=False, db_index = True)
    subtype = models.CharField(_('Type of Opportunity'), max_length=50, choices=OPPORTUNITY_SUB_TYPES, null=True,db_index = True)
    deadline = models.DateTimeField(null=False, db_index = True)
    
    def type_for_url(self):
        return "opportunities"

    def calendar_day(self):
        return self.deadline

    def can_edit(self):
        now = datetime.datetime.now()
        if self.deadline > now:
            return True
        return False

    def save(self, *args, **kwargs):
        self.subtype = strip_tags(self.subtype)
        super(Opportunity, self).save(*args, **kwargs)

class Job(AnnounceModel):
    type = models.CharField(max_length=50, default='job', editable=False,db_index = True)
    subtype = models.CharField(_('Type of Job'), choices= JOB_SUB_TYPES, max_length=50,db_index = True)
    deadline = models.DateTimeField(null=False)
    
    def type_for_url(self):
        return "jobs"
    
    def calendar_day(self):
        return self.deadline
    
    def save(self, *args, **kwargs):
        self.subtype = strip_tags(self.subtype)
        super(Job, self).save(*args, **kwargs)
                           
    def is_paid(self):
        payment = None
        
        try:
            payment = JobPostingPayment.objects.get(job=self)
        except:
            payments = JobPostingPayment.objects.filter(job=self)[:1]
            for p in payments:
                payment = p
                                     
        return payment

    def can_edit(self):
        now = datetime.datetime.now()
        if self.deadline > now:
            return True
        return False

class JobPostingPayment(models.Model):
    user = models.ForeignKey(User, null=False)
    job = models.ForeignKey(Job, null=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    created = models.DateTimeField(null=False, editable=False)   

    def formatted_amount(self):
        return "%01.2f" % self.amount

    def send_receipt(self):
        receipt = EmailMessage()
        receipt.to = ["%s" % self.user.email]
        receipt.bcc = [admin[1] for admin in settings.ADMINS]
        receipt.subject = "Rhizome.org Jobs Board Posting Payment Receipt"
        receipt.body = """
Dear %s,

This confirms your payment to Rhizome in the amount of $%s for a Job Posting.

Job Title: %s
Job Posting URL: http://rhizome.org%s
Payment Amount: $%s
Payment Date: %s

Thank your for using Rhizome.org.

Sincerely,

The Rhizome Staff

""" % (self.user.get_profile(), self.amount, self.job.title, self.job.get_absolute_url(), self.formatted_amount(), self.created.strftime("%m/%d/%Y"))
        receipt.send(fail_silently=False)
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.created = datetime.datetime.now()
        super(JobPostingPayment, self).save(*args, **kwargs)

class EventModerator(AnnounceModelModerator):
    pass

class JobModerator(AnnounceModelModerator):
    pass

class OpportunityModerator(AnnounceModelModerator):
    pass

moderator.register(Event, EventModerator)
moderator.register(Job, JobModerator)
moderator.register(Opportunity, OpportunityModerator)

class AnnounceCalendar(HTMLCalendar):
    '''
    this is the calendar on the community page
    '''
    def __init__(self, announcements):
        super(AnnounceCalendar, self).__init__()
        self.announcements = self.group_by_day(announcements)
        self.firstweekday = calendar.SUNDAY
        
    def formatday(self, day, weekday):
        if day != 0:
            #cssclass = self.cssclasses[weekday]
            cssclass = "day-number"
            if date.today() == date(self.year, self.month, day):
                cssclass += ' today'
            if day in self.announcements:
                cssclass += ' calendar-lookup-day'
                body = ['']
                announcement_date = ''
                for announcement in self.announcements[day]:
                    try:
                        announcement_date = announcement.start_date
                    except:
                        try:
                            announcement_date = announcement.deadline
                        except:
                            announcement_date = announcement.created
                    #body.append(esc(announcement.type))
                return self.day_cell(cssclass, announcement_date, '%d %s' % (day, ''.join(body)))
            return self.day_cell(cssclass, None, day)
        return self.day_cell('noday',None, '&nbsp;')

    def formatmonth(self, year, month):
        self.year, self.month = year, month
        
        return super(AnnounceCalendar, self).formatmonth(year, month)

    def group_by_day(self, announcements):
#         field = lambda announcement: announcement.created.day
        field = lambda announcement: announcement.calendar_day().day
        
        return dict(
            [(day, list(items)) for day, items in groupby(announcements, field)]
        )

    def day_cell(self, cssclass, announcement_date, body):
        if announcement_date:
            return '<td class="%s" rel = "%s/%s/%s"><span>%s</span></td>' % (cssclass, announcement_date.year, announcement_date.month, announcement_date.day, body)   
        else:
             return '<td class="%s"><span>%s</span></td>' % (cssclass, body)



#####
###ANNOUNCEMENT FUNCTIONS
######

def get_latest_announcements(limit=None):

    if limit:
        objects_per_limit = int(limit) / 3
        
        events = Event.objects \
            .filter(status=True) \
            .exclude(is_spam=True) \
            .order_by('-created') \
            [:objects_per_limit]
        
        opportunitys = Opportunity.objects \
            .filter(status=True) \
            .exclude(is_spam=True) \
            .order_by('-created') \
            [:objects_per_limit]
        
        jobs = Job.objects \
            .filter(status=True) \
            .exclude(is_spam=True) \
            .order_by('-created') \
            [:objects_per_limit]
    else:
        events = Event.objects \
            .filter(status=True) \
            .order_by('-created') \
            .exclude(is_spam=True)
        
        opportunitys = Opportunity.objects \
            .filter(status=True) \
            .order_by('-created') \
            .exclude(is_spam=True)
            
        jobs = Job.objects \
            .filter(status=True) \
            .order_by('-created') \
            .exclude(is_spam=True)
        
    return sorted(chain(events, opportunitys, jobs), key=attrgetter('created'), reverse=True)

def get_announcements_by_deadline(limit=None):
    today = datetime.date.today()
        
    opportunitys = Opportunity.objects \
        .filter(status=True) \
        .filter(status=1) \
        .filter(deadline__gte = today) \
        .exclude(is_spam=True)
    
    jobs = Job.objects \
        .filter(status=True) \
        .filter(deadline__gte = today) \
        .exclude(is_spam=True) \
        
    result = sorted(chain(opportunitys, jobs), key=attrgetter('deadline'), reverse=False)
    if limit:
        return result[:limit]
    return result

def get_latest_jobs(limit):
    today = datetime.date.today()
    latest_jobs = Job.objects \
        .order_by('-created') \
        .filter(status=1) \
        .exclude(is_spam=True) \
        .filter(deadline__gte = today)[:limit]
    return latest_jobs

def get_random_jobs(limit):
    today = datetime.date.today()
    random_jobs = Job.objects \
        .order_by('-created') \
        .filter(status=1) \
        .exclude(is_spam=True) \
        .filter(deadline__gte = today) \
        .order_by('?')[:limit]
    return random_jobs
    
def get_latest_opportunities(limit):
    latest_opportunitys = Opportunity.objects \
        .order_by('-created') \
        .filter(status=1) \
        .exclude(is_spam=True)[:limit]
    return latest_opportunitys
    
def get_latest_events(limit):
    latest_events = Event.objects \
        .order_by('-created') \
        .filter(status=1) \
        .exclude(is_spam=True)[:limit]
    return latest_events

def get_events_and_opportunities(limit):
    if limit:
        objects_per_limit = floor(int(limit) / 2)
    opportunities = get_latest_opportunities(objects_per_limit)
    events = get_latest_events(objects_per_limit)
    announcements = sorted(chain(opportunities, events), key=attrgetter('created'), reverse=False)
    return announcements

def get_current_events(limit):
    now = datetime.datetime.now()
    ahead = datetime.timedelta(days=3)
    behind = datetime.timedelta(days=-150)
    events = Event.objects \
        .filter(start_date__lte=now+ahead, start_date__gte=now+behind) \
        .filter(status=1) \
        .exclude(is_spam=True) \
        .order_by("-start_date")[:limit]
    return events
    
def get_latest_opps(limit):
    even_split = floor(int(limit) / 2)
    latest_calls = Opportunity.objects \
        .order_by('-created') \
        .filter(status=1) \
        .exclude(is_spam=True)[:even_split  + 1]
        
    latest_jobs = Job.objects \
        .order_by('-created') \
        .filter(status=1) \
        .exclude(is_spam=True)[:even_split]
    opps = sorted(chain(latest_calls, latest_jobs), key=attrgetter('created'), reverse=True)        
    return opps
    
def get_announce_calendar():
    today = datetime.date.today()
    events = Event.objects \
        .filter(status=True) \
        .filter(start_date__year=today.year, start_date__month= today.month) \
        .filter(status=1) \
        .order_by('start_date') 
    announce_calendar = AnnounceCalendar(events).formatmonth(today.year, today.month)
    return announce_calendar

# signals
def update_activity_stream(sender, instance, **kwargs):
    # Used to update stream, not used by comments (see discuss.signals)
    
    try: # check to make sure it's a published object
        activity_status = instance.status
    except:
        try:
            activity_status = instance.is_visible
        except:
            activity_status = False
    
    if activity_status: # if published, check to make sure the object's corresponding activity doesn't already exist
        try:
            activity_check = ActivityStream.objects.get(content_type=ContentType.objects.get_for_model(instance), object_pk=instance.id)
        except:
            activity_check = False
        
        if not activity_check:
            activity = ActivityStream()    
            activity.user = instance.user
            activity.created = datetime.datetime.now()
            activity.content_type = ContentType.objects.get_for_model(instance)
            activity.object_pk = instance.id
            activity.save()


post_save.connect(update_activity_stream, sender=Job, dispatch_uid='update_job_activity')
post_save.connect(update_activity_stream, sender=Event, dispatch_uid='update_event_activity')
post_save.connect(update_activity_stream, sender=Opportunity, dispatch_uid='update_opportunity_activity')