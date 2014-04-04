import datetime
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User 
from django.core.exceptions import MultipleObjectsReturned
from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver

from eazyemail.models import EazyEmail


ccType=(
    ('----','----'),
    ('MC','MasterCard'),
    ('Visa','Visa'),
    ('AmEx','American Express')
)

AutoEmailChoices = (
    ('60_day_conversion','60 Day Conversion Email'),
    ('30_day_conversion','30 Day Conversion Email'),
    ('30_day_renewal','30 Day Expiration Reminder'),
    ('15_day_renewal','15 Day Expiration Reminder'),
    ('day_of_renewal','Day of Expiration Reminder'),
    ('comeback_email','Comeback Email'),
    ('council_level_donation','Council Level Donation'),
    ('high_level_donation','High Level Donation'),
    ('regular_donation','Regular Membership Donation'),
    ('patron_donation','Patron Membership Donation'),
    ('user_donation','User Level Donation'),
    ('user_welcome_email','User Welcome Email'),
    ('artbase_congrats_email','ArtBase Curated Congrats Email'),
)

def get_membership_level_upload_to(self, filename):
    return 'support/membership_levels/%s/%s' % (self.title.replace(' ', '-').lower(), filename.replace(' ', '-').lower())
    
class AnnualSupporters(models.Model):
    year = models.IntegerField(max_length=10)
    root_level = models.TextField(help_text='Gave $1000', blank=True, null=True)
    stolon_level = models.TextField(help_text='Gave $500-999', blank=True, null=True)
    bud_level = models.TextField(help_text='Gave $250-$499', blank=True, null=True)
    seedling_level = models.TextField(help_text='Gave $100-249', blank=True, null=True)
    sprout_level = models.TextField(help_text='Gave $50-99', blank=True, null=True)
    membership_level = models.TextField(help_text='Gave $25-49+', blank=True, null=True)
    institutions = models.TextField(help_text="Agencies and Institutions", blank=True, null=True)
    corporate = models.TextField(help_text='Corporate Sponsers', blank=True, null=True)
    is_active = models.BooleanField(help_text='Is this the current list?')

    def __unicode__(self):
        return 'year: %s' % (self.year)
        
def get_current_supporters():
    supporters = AnnualSupporters.objects.filter(is_active=True).order_by('-year')[:1]
    for s in supporters:
        return s

class CommunityCampaignManager(models.Manager):
     def current(self):
        campaigns = self.filter(is_active=True)
        if campaigns:
            return campaigns[0]
        return None

class CommunityCampaign(models.Model):
    year = models.IntegerField(max_length=10)
    is_active = models.BooleanField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    amount_goal = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    objects = CommunityCampaignManager()

    class Meta:
        ordering = ('-year',)

    @property
    def donations(self):
        return NewDonation.objects.filter(created__gte=self.start_date, created__lte=self.end_date)

    @property
    def percent_raised(self):
        result = self.amount_raised / self.amount_goal * 100
        return int(round(result))

    @property
    def amount_raised(self):
        result = self.donations.aggregate(Sum('amount'))
        if result.get('amount__sum'):
            return result['amount__sum']
        return Decimal('0.00')

    @property
    def formatted_amount_raised(self):
        return '${:,.0f}'.format(self.amount_raised)

    @property
    def formatted_amount_goal(self):
        return '${:,.0f}'.format(self.amount_goal)
    
    @property
    def days_left(self):
        days = (self.end_date - datetime.datetime.today()).days
        if days > 0:
            return days;
        return 0

class MembershipBenefit(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(help_text='The Detailed Explanation', null=True, blank=True)
    summary = models.TextField(help_text='Keep it short and sweet')
    is_active = models.BooleanField()
    link = models.URLField(blank=True, null=True)

    def __unicode__(self):
        return '%s' % self.title

class MembershipLevel(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(help_text='The Detailed Explanation', null=True, blank=True)
    summary = models.TextField(help_text='Keep it short and sweet')
    is_active = models.BooleanField()
    link = models.URLField(blank=True, null=True)
    benefits = models.ManyToManyField(MembershipBenefit, blank=True,null=True)
    donation_level = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    internal_title = models.CharField(help_text='Do Not Edit', max_length=20)
    icon_one = models.ImageField(upload_to = get_membership_level_upload_to,
        help_text='MUST SAVE BEFORE ADDING!!!!!!', null=True, blank=True)
    icon_two = models.ImageField(upload_to = get_membership_level_upload_to,
        help_text='MUST SAVE BEFORE ADDING!!!!!!', null=True, blank=True)
    badge = models.ImageField(upload_to = get_membership_level_upload_to,
        help_text='MUST SAVE BEFORE ADDING!!!!!!', null=True, blank=True)

    def get_benefits(self):
        return self.benefits.all()

    def __unicode__(self):
        return '%s' % self.title
        
class AutoGeneratedEmail(models.Model):
    email_title = models.CharField(max_length=100, choices=AutoEmailChoices)    
    email_body =  models.TextField(help_text='DO NOT COPY/PASTE FROM TEXT EDITOR! MUST BE PLAIN TEXT. WATCH OUT FOR APOSTROPHES.')
    email_description =  models.TextField(help_text='What\'s the context/purpose of this email?')

    def __unicode__(self):
        return '%s' % self.email_title

class NewDonation(models.Model):
    CHECK = 'CK'
    CREDIT_CARD = 'CC'
    ELECTRONIC_FUNDS_TRANSFER = 'EFT'
    CASH = 'Cash'
    BITCOIN = 'BTC'
    PAYMENT_METHOD_CHOICES = (
        (CHECK, 'Check'),
        (CREDIT_CARD, 'Credit Card'),
        (ELECTRONIC_FUNDS_TRANSFER, 'Electronic Funds Transfer'),
        (CASH, 'Cash'),
        (BITCOIN, 'Bitcoin'),
    )

    amount = models.DecimalField(help_text='USD', max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=30, blank=True, choices=PAYMENT_METHOD_CHOICES, default=CREDIT_CARD)
    created = models.DateTimeField(blank=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(blank=True)
    authorize_transaction_id = models.CharField(max_length=255, blank=True)
    authorize_transaction_raw_response = models.TextField(blank=True)
    gift = models.CharField(max_length=255, blank=True)
    via_paypal = models.BooleanField()
    paypal_transaction_id = models.CharField(max_length=255, blank=True)
    paypal_transaction_raw_response = models.TextField(blank=True)

    def __unicode__(self):
        if self.first_name or self.last_name:
            return '%s %s' % (self.first_name, self.last_name)
        return '%s' % self.id 

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = datetime.datetime.now()

        from accounts.models import RhizomeUser
        if not self.pk:
            if self.contact_email:
                try:
                    self.user = RhizomeUser.objects.get(email=self.contact_email)
                except (RhizomeUser.DoesNotExist, MultipleObjectsReturned):
                    pass
        return super(NewDonation, self).save(*args, **kwargs)

#signals
@receiver(post_save, sender=NewDonation, dispatch_uid='support.update_donor_membership')
def update_donor_membership(sender, instance, created, **kwargs):
    if created:
        if Decimal(instance.amount) >= Decimal(settings.MIN_DONATION_TO_BECOME_MEMBER):
            if instance.user:
                membership = instance.user.get_profile().membership()
                
                if membership:
                    membership.update_membership(instance)
                else:
                    instance.user.get_profile().make_member(instance)
            elif instance.contact_email:
                email = EazyEmail.objects.get(title='Claim Membership Instructions')
                email.send(settings.MEMBERSHIP_GROUP_EMAIL, [instance.contact_email], bcc=[settings.MEMBERSHIP_GROUP_EMAIL], extra_context={
                    'first_name': instance.first_name,
                    'last_name': instance.last_name,
                    'donation_amount': instance.amount,
                })

@receiver(post_save, sender=NewDonation, dispatch_uid='support.send_donation_receipt')
def send_donation_receipt(sender, instance, created, **kwargs):
    if created:
        if Decimal(instance.amount) >= Decimal(settings.MIN_DONATION_TO_BECOME_COUNCIL):
            title = 'Council Level Donation'
        elif Decimal(instance.amount) >= Decimal(settings.HIGH_LEVEL_DONATION_CUTOFF):
            title = 'High Level Donation'
        elif Decimal(instance.amount) >= Decimal(settings.MIN_DONATION_TO_BECOME_MEMBER):
            title = 'Member Level Donation'
        else:
            title = 'User Level Donation'

        email = EazyEmail.objects.get(title=title)
        email.send(settings.MEMBERSHIP_GROUP_EMAIL, [instance.contact_email], bcc=[settings.MEMBERSHIP_GROUP_EMAIL], extra_context={
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'donation_amount': instance.amount,
            'current_year': datetime.datetime.now().year,
            'membership_price': settings.MIN_DONATION_TO_BECOME_MEMBER,
        })
