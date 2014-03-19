import datetime

from accounts.models import RhizomeMembership
from support.models import Donation

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand, CommandError


def send_expired_email(membership):
    email = EmailMessage()
    email.subject = "Your Rhizome membership has expired."
    email.to = [membership.user.email]
    email.bcc = [admin[1] for admin in settings.ADMINS] 
    email.body = """
Dear %s,

Did you notice that your Rhizome Membership expired?

You can renew quickly and easily here:

https://rhizome.org/support/donate/

You're missing out on all those great benefits that come with Rhizome Membership. Indispensable Resources where you can find educational programs, syllabi and residencies from around the globe to deepen your knowledge and skills. View hundreds of proposals and cast your vote for Rhizome's annual Commissions program. Flex your curator muscles with your very own Member Exhibition. Interact with artists and artworks in our comprehensive archive by leaving comments, saving artworks to your profile and access to full artwork records with the ArtBase Special Features. And on top of all that, a bonus 10 percent discount on all your purchases at the New Museum Store. 

http://rhizome.org/support/individual/

Seriously, it only takes a minute to click here and renew now! 

https://rhizome.org/support/donate/

Sincerely,

Rhizome

P.S. If you have made a donation within the past year, you are probably receiving this email because you have multiple records in our database.  If this is the case then no further action needs to be taken. Please contact %s if you believe that there has been an error that should be resolved or needs to be investigated.

+ + +

Rhizome.org is a not-for-profit 501(c)(3) organization. For U.S. taxpayers, contributions to Rhizome are tax-deductible, minus the value of any goods or services received, to the extent allowed by law.
""" % (membership.user.get_profile(), settings.SUPPORT_CONTACT[1])

    email.send(fail_silently=False)


class Command(BaseCommand):
    """
    This is a one-time blast used to catch up members who may not have been receiving email notices after new site launch in early 2011. Sends them expired emails. Sets expiration tools to False. 
    """

    def handle(self, *args, **options):
        now = datetime.datetime.now()
        expired_range = now - datetime.timedelta(90)
        safety_range = now - datetime.timedelta(15)
        one_year_ago = now - datetime.timedelta(365)
        
        expired_members = RhizomeMembership.objects \
            .filter(member_tools_exp_date__gte = expired_range) \
            .filter(member_tools_exp_date__lte = now) \
            .filter(complimentary = False) \
            .filter(org_sub_admin=False) \
            .filter(archival_access = False) \
            .filter(member_tools = False) \
            .filter(org_sub = None)\
            .exclude(last_reminder_email__gte = safety_range) \
            .exclude(last_homecoming_email__gte = safety_range) \
            .exclude(last_donation__created__gte = one_year_ago) 
        
        if expired_members:
            emails = []
            for membership in expired_members:
                send_expired_email(membership)
                membership.last_homecoming_email = datetime.datetime.now()
                membership.last_reminder_email = datetime.datetime.now()
                membership.member_tools = 0
                membership.archival_access   = 0                
                membership.save()
                emails.append('%s' % membership.user.email)
                
            email_string = ', '.join(["%s" % e for e in emails])  
            results = '%s members received expiration emails: %s' % (len(emails), email_string)
        else:
            results = 'no members received expiration emails'     

        mail_admins(
            'Send Expired Emails Cron', 
            '%s' % results
        ) 
