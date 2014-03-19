from itertools import chain
import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMessage
from django.db.utils import IntegrityError

from orgsubs.models import Organization, ProspectiveUser
from accounts.models import RhizomeMembership
from support.models import MembershipLevel, NewDonation

class Command(BaseCommand):
    """
    CRON JOB FOR 
        - UPDATING EXPIRED ORGSUB ACCOUNTS
        - ATTACHING USER ACCOUNTS TO ORGSUBS IF THAT ACCOUNT HAS AN ORGSUB EMAIL BUT IS NOT YET A PART OF AN ORGSUB
        
    SHOULD BE DONE OVERNIGHT EVERY NIGHT...
    """
    
    def handle(self, *args, **options):
        self.update_expired_orgsub_accounts()
        self.add_user_to_orgsub()
        self.send_reminder_to_prospective_users()

    def update_expired_orgsub_accounts(self):
        # UPDATES EXPIRED ORGSUB ACCOUNTS

        today = datetime.datetime.now()
        today_minus_year = (datetime.datetime.today() - datetime.timedelta(365))

        expired_org_subs = Organization.objects.filter(expiration_date__lte = today).filter(complimentary=False)
        orgsub_membership_level = MembershipLevel.objects.get(internal_title="orgsub")
        #orgsubs_that_expire_today = [Organization.objects.get(id=70)]

        for orgsub in expired_org_subs:
            orgsub.active = False
            orgsub.save()
            affected_members = RhizomeMembership.objects \
                .filter(org_sub = orgsub) \
                .filter(org_sub_admin=False) \
                .filter(complimentary=False) \
                .order_by('-org_sub')

            for member in affected_members:            
                
                try:
                    #check first to see if the member has donated on their own
                    donation = NewDonation.filter(user=member.user)[0]
                except:
                    donation = None
                    
                if donation:
                    # if the member has made a donation, handle them differently
                    
                    if donation.created < today_minus_year:
                        # set memberships as expired for currenlty active members with old donation...
                        if member.member_tools == 1:
                            member.archival_access = 0
                            member.member_tools = 0
                            member.membership_level = orgsub_membership_level
                            member.archival_access_exp_date = today
                            member.member_tools_exp_date = today
                            member.save() 
                    else:
                         # if donation not older than a year ago, don't change them...
                        pass
                    
                else:
                    member.archival_access = 0
                    member.member_tools = 0
                    member.archival_access_exp_date = today
                    member.member_tools_exp_date = today
                    member.save()

                    

    def add_user_to_orgsub(self):
        #ATTACHES USER ACCOUNTS TO ORGSUBS IF THAT ACCOUNT HAS AN ORGSUB EMAIL BUT IS NOT YET APART OF AN ORGSUB
        orgsub_email_domains_list = list(
            ((org_sub_networks["email_domain"]).split("," )) for org_sub_networks in Organization.objects \
                .filter(auto_add_email_subscription=True) \
                .filter(active=True) \
                .filter(cancelled=False) \
                .values("email_domain")          
            )
        email_domains_flattened = list(chain.from_iterable(email_domain for email_domain in orgsub_email_domains_list)) 

        for email_domain in email_domains_flattened:
            orgsub = Organization.objects.get(email_domain__icontains=email_domain)
            users_with_email_domain = User.objects.raw("SELECT * FROM auth_user WHERE email REGEXP '.%s';" % email_domain)
            
            for user in users_with_email_domain:
        
                try:
                    membership = RhizomeMembership.objects.get(user=user)            
                except:
                    membership = None
                
                if membership:
                    if not user.username == 'testuser':        
                        membership.make_orgsub_member(orgsub)
                                        
                    elif membership.org_sub != orgsub:
                        # "++++not a match++++"
                        pass
                    else:
                        #already orgsub member
                        pass
                    
                else:
                    user.get_profile().make_orgsub_member(orgsub)
                    
    def send_reminder_to_prospective_users(self):
        today = datetime.datetime.today()
        ninety_days_ago = (today - datetime.timedelta(90))
        thirty_days_ago = (today - datetime.timedelta(30))
        
        # get prospects created in last 3 months that haven't accepted
        # only email them once a month
        prospective_users = ProspectiveUser.objects.filter(
                created__gte = ninety_days_ago,          
                last_invitation__lte = thirty_days_ago,          
                accepted = False
            )
                    
        for prospect in prospective_users:
            if "," in prospect.email:
                try:
                    prospect.save()
                
                except IntegrityError, e:
                    if e[0] == 1062:
                        # it's a duplicate
                        prospect.delete()
                    else:
                        pass
            
            self.send_reminder_to_prospect(prospect)
            prospect.last_invitation = today
            prospect.save()

    def send_reminder_to_prospect(self, prospect):
        admin = prospect.invite_admin
        reminder = EmailMessage()
        reminder.subject = "Reminder: You've been invited to join Rhizome!"
        reminder.to = [prospect.email]
        reminder.bcc = [admin[1] for admin in settings.ADMINS]
        invite_url = "http://rhizome.org/welcome/orgsub/?email=%s&registration_code=%s" % (prospect.email, prospect.registration_code)

        reminder.body = """
Hi there, 

Just a reminder...

%s (%s) has just offered you a membership as part of the %s membership for Rhizome.org. 

Rhizome.org is a global arts platform, and your group membership allows you access to Rhizome *without* having to give a donation. (All Rhizome members are required to support the organization with an annual gift; group memberships are purchased by institutions such as schools, media centers, or libraries). 

Clicking on the link below will validate your account and give you access to our publications, discussion groups, ArtBase archive, community directory, and other features:

%s 

Thanks and welcome to Rhizome, 

The Rhizome Crew""" % (admin, admin.email, prospect.org_sub, invite_url )         
        reminder.send(fail_silently=False)

