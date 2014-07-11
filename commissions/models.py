import datetime

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.utils.html import strip_tags
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import File
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.utils.text import slugify

from countries.models import Country, UsState
from artbase.models import ArtworkStub

class CycleManager(models.Manager):
    def current(self):
        return self.filter(is_active=True).order_by('-submission_start_date')

    def past(self):
        return self.filter(is_active=False, submission_end_date__lte=datetime.datetime.now()).order_by('-submission_start_date')

class Cycle(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(null=True, blank=True)
    procedures = models.TextField(null=True, blank=True)
    is_tumblr_commission = models.BooleanField(help_text='Is this a Tumblr commission?')
    is_active = models.BooleanField(help_text=_('Is this cycle current?'))
    submission_start_date = models.DateTimeField(null=True,blank=True, db_index=True)
    submission_end_date = models.DateTimeField(null=True,blank=True, db_index=True)
    approval_vote_start = models.DateTimeField(blank=True)
    approval_vote_end = models.DateTimeField(blank=True)
    ranking_vote_start = models.DateTimeField(null=True,blank=True,db_index=True)
    ranking_vote_end =  models.DateTimeField(null=True,blank=True,db_index=True)
    finalists_count = models.IntegerField(default=0, blank=True) # actual number of finalists
    winner_proposal_deprecated = models.ForeignKey('Proposal',null=True,blank=True,related_name="deprecated_winner",help_text=_('Deprecated. Only used on old commissons cycles. Current cycles have jury/user vote winners.'))
    winner_artwork  = models.ManyToManyField(ArtworkStub, null=True, blank=True, help_text=_('If no proposal is available. Current cycles have jury/user vote winners linked to proposals.'))
    jury_award_winners_proposal = models.ManyToManyField('Proposal',null=True,blank=True,related_name="jury_award_winners")
    user_vote_winners_proposal  = models.ManyToManyField('Proposal',null=True,blank=True,related_name="user_vote_winners")
    supporters = models.TextField(blank=True, null=True)
    objects = CycleManager()

    def __unicode__(self):
        return '%s: %s' % (self.id,self.title)
    
    def vote_url(self):
        return '/commissons/voting/%s' % self.id
    
    def submit_url(self):
        return '/commissons/submit/%s' % self.id

    def jury_winners(self):
        return self.jury_award_winners_proposal.all()
    
    def vote_winners(self):
        return self.user_vote_winners_proposal.all()
        
    def winners_artwork(self):
        return self.winner_artwork.all()

    def get_proposals(self):
        return Proposal.objects.filter(cycle=self, submitted=True)

    def get_public_proposals(self):
        return Proposal.objects.filter(cycle=self, submitted=True, is_public=True)

    def get_finalist_proposals(self):
        return Proposal.objects.filter(cycle=self, finalist=True)

    def get_rank_vote_finalist_proposals(self):
        return Proposal.objects.filter(cycle=self, rank_vote_finalist=True)

def get_commissions_upload_to(self, filename):
    extension = filename.split('.')[-1]
    fixed_title = slugify(self.title[:30])
    return 'commissions/proposals/%s/%s/%s.%s' % (self.cycle.id, self.author.id, fixed_title, extension)  

def get_thumb_upload_to(self, filename):
    extension = filename.split('.')[-1]
    fixed_title = slugify(self.title[:30])
    return 'commissions/proposals/%s/%s/thumb-%s.%s' % (self.cycle.id, self.author.id, fixed_title, extension)  


class ProposalManager(models.Manager):
    def current(self):
        return self.filter(cycle__in=Cycle.objects.current(), submitted=True)

    def current_finalists(self):
        return self.filter(cycle__in=Cycle.objects.current(), submitted=True, finalist=True)

    def current_rank_vote_finalists(self):
        return self.filter(cycle__in=Cycle.objects.current(), submitted=True, rank_vote_finalist=True)

class Proposal(models.Model):
    title = models.CharField(max_length=225)
    artists = models.ManyToManyField(User,null=True,blank=True,related_name="artists involved in proposal with user accts")
    other_artists = models.TextField(max_length=150,null=True, blank=True)
    author = models.ForeignKey(User,related_name="proposals")
    external_url = models.URLField(blank=True,null=True)
    tumblr_url = models.URLField(blank=True, null=True)
    rhizome_hosted = models.BooleanField(default=1, blank=True,db_index=True) 
    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField(editable=False)
    cycle = models.ForeignKey('Cycle')
    summary = models.TextField(max_length=150,null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    timeline_and_budget = models.TextField(null=True, blank=True)
    resume_or_cv = models.TextField(null=True, blank=True)
    work_samples = models.TextField(null=True, blank=True)
    is_public = models.BooleanField(default=1, blank=True,db_index=True)
    submitted = models.BooleanField(default=0, blank=True,db_index=True)
    deleted = models.BooleanField(default=0, blank=True)
    allow_comments = models.BooleanField(default=1, blank=True,db_index=True)
    finalist = models.BooleanField(default=0)
    rank_vote_finalist = models.BooleanField(default=0)
    city = models.CharField(max_length=255, null=True,blank=True)
    username = models.CharField(max_length=255, blank=True, null=True,help_text=_('Deprecated. User should be used instead.'))
    legacy_state = models.CharField(max_length=100, blank=True, null=True,editable=False) #leftover 
    legacy_country = models.CharField(max_length=100, blank=True, null=True,editable=False) #leftover
    state = models.ForeignKey(UsState,to_field='name',null=True, blank=True)
    country = models.ForeignKey(Country,null=True,blank=True)    
    #created in view from image
    thumbnail =  models.ImageField(upload_to = get_thumb_upload_to, null=True, blank=True)   
    image = models.ImageField(upload_to = get_commissions_upload_to, null=True, blank=True)

    objects = ProposalManager()

    def __unicode__(self):
        return 'Commissions Proposal: %s' % (self.title,)
    
    def get_artists(self):
        return self.artists.all()

    def get_all_involved(self):
        involved = [x for x in self.get_artists()]
        involved.append(self.author)
        if self.other_artists:
            involved.append(self.other_artists)
        return involved

    def get_absolute_url(self):
        return '/commissions/proposal/%s/' % self.id

    def edit_url(self):
        return '/commissions/proposal/%s/edit/' % self.id

    def view_url(self):
        if not self.rhizome_hosted:
            return '%s' % self.external_url
        else:
            return reverse('commissions_proposal_detail', args=[self.id])
   
    def voting_view_url(self):
        if not self.rhizome_hosted:
            return '%s' % self.external_url
        else:
            return '/commissions/proposal/%s/voting_view/' % self.id

    def app_voting_view_url(self):
        return '/commissions/voting/approval/?proposal=%s' % self.id
    
    def get_approval_votes(self):
        return ApprovalVote.objects.filter(proposal=self)

    def get_approval_votes_count(self):
        return ApprovalVote.objects.filter(proposal=self).count()

    def get_is_approved_votes_count(self):
        return ApprovalVote.objects.filter(proposal=self).filter(approved=True).count()
        
    def get_not_approved_votes_count(self):
        return ApprovalVote.objects.filter(proposal=self).filter(approved=False).count()

    def get_rank_votes(self):
        return RankVote.objects.filter(proposal=self)

    def get_rank_votes_count(self):
        return RankVote.objects.filter(proposal=self).count()

    def admin_artists(self):
        for d in self.artist.all():
            return '%s / %s' % (d.get_full_name, d.username)
    
    admin_artists.short_description = 'Artist(s)'

    def content_type_id(self):
        ct = ContentType.objects.get_for_model(self)
        return ct.id
    
    def content_type(self):
        ct = ContentType.objects.get_for_model(self)
        return ct

    def send_created_proposal_notification_email(self):
        proposal_notification_email = EmailMessage()
        proposal_notification_email.to = [self.author.email]
        proposal_notification_email.subject = "Rhizome Commissions Proposal Created"
        current_site = Site.objects.get_current()
        proposal_edit_url = "http://%s%s" % (current_site.domain, self.edit_url())        

        proposal_notification_email.body = """
Dear %s,

Thank you for creating a commissions proposal as part of the %s. 

You may edit this proposal at any time up until %s via this url:

%s

Good luck!

-The Rhizome Team


""" % (self.author.get_profile(), self.cycle.title, self.cycle.submission_end_date.strftime("%m/%d/%Y"), proposal_edit_url)
        proposal_notification_email.send(fail_silently=True)

    def send_published_proposal_notification_email(self):
        proposal_notification_email = EmailMessage()
        proposal_notification_email.to = [self.author.email]
        proposal_notification_email.subject = "Rhizome Commissions Proposal Published"
        current_site = Site.objects.get_current()
        proposal_edit_url = "http://%s%s" % (current_site.domain, self.edit_url())     
        proposal_view_url = "http://%s%s" % (current_site.domain, self.get_absolute_url())                    
        proposal_notification_email.body = """
Dear %s,

Your Rhizome commissions proposal, "%s", has been published on Rhizome as part of the %s. 

You can view your proposal at this url: 

%s

You may edit your proposal at any time up until %s via this url: 

%s

Good luck!

-The Rhizome Team


""" % (self.author.get_profile(), self.title, self.cycle.title, proposal_view_url, self.cycle.submission_end_date.strftime("%m/%d/%Y"), proposal_edit_url )
        proposal_notification_email.send(fail_silently=True)

    def save(self, *args, **kwargs):
        ''' On save, strip html and update timestamps '''
        if not self.id:
            self.created = datetime.datetime.now()
        self.modified = datetime.datetime.now()
        self.description = strip_tags(self.description)
        self.timeline_and_budget = strip_tags(self.timeline_and_budget)
        self.summary = strip_tags(self.summary)
        self.resume_or_cv = strip_tags(self.resume_or_cv)
        self.work_samples = strip_tags(self.work_samples)
        super(Proposal, self).save(*args, **kwargs)

def send_proposal_created_email(sender, instance, created, **kwargs):
    if created:
        instance.send_created_proposal_notification_email()
post_save.connect(send_proposal_created_email,sender=Proposal,dispatch_uid = 'commissions.proposal')

'''
Approval votes are the first part of user voting, when users go through and vote for ALL proposals.
'''
class ApprovalVote(models.Model):
    user = models.ForeignKey(User)
    proposal = models.ForeignKey(Proposal)
    approved = models.BooleanField(default=0)
    created = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = datetime.datetime.now()
        super(ApprovalVote, self).save(*args, **kwargs)

    class Meta:
        unique_together = ("user", "proposal")
        
    def __unicode__(self):
        return '%s for  %s' % (self.id, self.proposal)

'''
Approval votes are the second part of users voting, when users rank the 25 finalists.
'''

class RankVote(models.Model):
    user = models.ForeignKey(User)
    proposal = models.ForeignKey(Proposal)
    rank = models.IntegerField(default=0)
    created = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = datetime.datetime.now()
        super(RankVote, self).save(*args, **kwargs)

       
    class Meta:
        unique_together = ("user", "proposal", "rank")
        
    def __unicode__(self):
        return '%s for  %s' % (self.id, self.proposal)

# ######## NEW COMMISSIONS

import json

from django import forms
from django.contrib.sites.models import Site
from django.core import validators
from django.core.validators import MaxLengthValidator

from eazyemail.models import EazyEmail


class GrantManager(models.Manager):
    def accepting_submissions(self):
        return self.filter(
            submission_start_date__lte=datetime.datetime.now(), 
            submission_end_date__gte=datetime.datetime.now()
        )

    def voting(self):
        return self.filter(
            voting_start_date__lte=datetime.datetime.now(),
            voting_end_date__gte=datetime.datetime.now()
        )

    def voting_ended(self):
        return self.filter(voting_end_date__lt=datetime.datetime.now())


class Grant(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    blurb = models.TextField()
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='grant/img/')
    voting_enabled = models.BooleanField(default=True)
    submission_start_date = models.DateTimeField(null=True, blank=True, db_index=True)
    submission_end_date = models.DateTimeField(null=True, blank=True, db_index=True)
    voting_start_date = models.DateTimeField(null=True, blank=True)
    voting_end_date = models.DateTimeField(null=True, blank=True)
    template = models.CharField(max_length=255, default='commissions/micro_grant_proposal.html')
    confirmation_email = models.ForeignKey(EazyEmail)

    objects = GrantManager()

    class Meta():
        ordering = ('-submission_start_date',)

    def __unicode__(self):
        return self.name

    @property
    def number_of_proposals(self):
        return self.proposals.count()

    @property
    def proposal_data_headers(self):
        headers = []
        for datum in self.proposal_data:
            for k, v in datum.items():
                headers.append(k)
        return list(set(headers))

    @property
    def proposal_data(self):
        return [p.data_dict for p in self.proposals.all()]

class GrantProposal(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    grant = models.ForeignKey(Grant, related_name='proposals')
    user = models.ForeignKey(User, related_name='grant_proposals')
    data = models.TextField(blank=True)
    image = models.ImageField(upload_to='grant_proposal/img/', blank=True)

    def __unicode__(self):
        return '%s: %s' % (self.grant, self.user)

    @property
    def data_dict(self):
        d = {}
        if self.data:
            d.update(json.loads(self.data))
        if self.image:
            d.update({'image': '%s%s' % (Site.objects.get_current().domain, self.image.url)})
        return d
        
@receiver(post_save, sender=GrantProposal, dispatch_uid='commissions.send_confirmation')
def send_confirmation(sender, instance, created, **kwargs):
    if created:
        instance.grant.confirmation_email.send(settings.DEFAULT_FROM_EMAIL, [instance.user.email], extra_context={
        })
