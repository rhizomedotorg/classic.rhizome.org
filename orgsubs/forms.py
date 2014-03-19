import datetime

from django.conf import settings
from django.core.mail import EmailMessage
from django import forms
from django.forms import ModelForm
from django.template import Context, loader
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from netaddr import cidr_to_glob, valid_glob

from orgsubs.models import *
from utils.helpers import make_random_string

def send_invitation_to_prospective_user(user_email, admin_name, admin_email, invite_url):
    invitation = EmailMessage()
    invitation.subject = "You've been invited to join Rhizome!"
    invitation.to = [user_email] 
    invitation.bcc = [admin[1] for admin in settings.ADMINS]
    invitation.body = """
Hi there, 
%s (%s) has just offered you a membership as part of a group membership at Rhizome.org. 

Rhizome.org is a global arts platform, and your group membership allows you access to Rhizome *without* having to give a donation. (All Rhizome members are required to support the organization with an annual gift; group memberships are purchased by institutions such as schools, media centers, or libraries). 

Clicking on the link below will validate your account and give you access to our publications, discussion groups, ArtBase archive, community directory, and other features:

%s 

Thanks and welcome to Rhizome, 

The Rhizome Crew""" % (admin_name, admin_email, invite_url )    

    invitation.send(fail_silently=False)


def send_invitation_to_member_via_register(user_email,registration_code):
    invitation = EmailMessage()
    invitation.subject = "Welcome to Rhizome!"
    invitation.to = [user_email]
    invite_url = "http://rhizome.org/welcome/?email=%s&registration_code=%s" % (user_email, registration_code)
    invitation.body = """
Hello, 

You have just registered as part of a group membership at Rhizome.org.
            
Rhizome.org is a global arts platform, and your group membership allows you access to Rhizome *without* having to give a donation. (All Rhizome members are required to support the organization with an annual gift; group memberships are purchased by institutions such as schools, media centers, or libraries).

Clicking on the link below will validate your account and give you access to our publications, discussion groups, ArtBase archive, community directory, and other features:

%s

If you'd like to make a donation to Rhizome, you may do so here once your account has been activated:

http://rhizome.org/support/donate/

Thank and welcome to Rhizome! 

The Rhizome Crew
    """ % (invite_url )    
    invitation.send(fail_silently=False)
    

######creates a list of orgsubs email adys for registration
ORGSUB_EMAILS = [("----","----")]
org_subs = Organization.objects.values("email_domain","email_domain")
for org_sub in org_subs:
    if org_sub["email_domain"]:
        email = org_sub["email_domain"].replace("*","")
        if (",") in email:
            email = email.split(',')
            if len(email) > 1:
                ORGSUB_EMAILS.append((email[0], email[0]))
        else:
            ORGSUB_EMAILS.append((email, email))
            
#######creates a list of orgsubs names for registration
ORGSUB_LIST = [("","")]
org_subs = Organization.objects.values("name","email_domain","id") \
    .exclude(cancelled=True).filter(active = True)
for org_sub in org_subs:
    if org_sub["email_domain"]:
        name = org_sub["name"]
        id = org_sub["id"]
        ORGSUB_LIST.append((id, name))            
            
#########
###EDIT ORGSUB FORM
#########
class EditOrgSubForm(ModelForm):
           
    class Meta:
        model = Organization
        exclude = ('email_domain','ip_networks','name','last_alert_sent','expiration_date',
                'notes','legacy_location','donation_required','start_date','size','rhiz_admin_contact_info')
       
    def __init__(self, *args, **kwargs):
        super(EditOrgSubForm, self).__init__(*args, **kwargs)

#########ADD MEMBER FORM     
class ManageMemberForm(forms.Form):
    '''
    takes an email address and send a welcome email (to verify the account) 
    with code and link to welcome page. once at welcome page, 
    the code is checked and if ok the account is created
    '''
    
    email_address = forms.EmailField()
    admin_email = forms.EmailField(widget=forms.HiddenInput)
    org = forms.IntegerField(widget=forms.HiddenInput)
    admin = forms.IntegerField(widget=forms.HiddenInput) 
        
    def __init__(self, *args, **kwargs):
        super(ManageMemberForm, self).__init__(*args, **kwargs)
    
    def save(self, *args, **kwargs):
        try:
            user_check = User.objects.get(email = self.cleaned_data.get("email_address"))
        except:
            user_check = False
        
        try:
            prospective_user_check = ProspectiveUser.objects.get(email = self.cleaned_data.get("email_address"))
        except:
            prospective_user_check = False
            
        if not user_check:
            if not prospective_user_check:
                prospective_user = ProspectiveUser(email = self.cleaned_data.get("email_address"))
                prospective_user.registration_code = make_random_string()
                prospective_user.last_invitation = datetime.datetime.now()
                prospective_user.org_sub = Organization.objects.get(id = self.cleaned_data.get("org"))
                admin = User.objects.get(id = self.cleaned_data.get("admin"))
                prospective_user.invite_admin = admin #so we can see who invited them
                prospective_user.accepted = 0
                invite_url = "http://rhizome.org/welcome/orgsub/?email=%s&registration_code=%s" % \
                    (self.cleaned_data.get("email_address"),prospective_user.registration_code)
                send_invitation_to_prospective_user(self.cleaned_data.get("email_address"), 
                        admin.get_full_name(), self.cleaned_data.get("admin_email"),invite_url )
                prospective_user.save()
                return "%s has been invited to join your organizational subscription"  % self.cleaned_data.get("email_address")
            else:
                return "%s has already been invited to join your organizational subscription" % self.cleaned_data.get("email_address")
        else:
            return "%s has already joined Rhizome" % self.cleaned_data.get("email_address")

#MEMBER REGISTER FORM
class OrgSubMemberRegisterForm(forms.Form):
    '''
    basically the same process as add member form, takes an email address 
    and sends a welcome email (to verify the account) with code and link to welcome page. 
    once at welcome page, the code is checked and if ok the account is created. 
    you can pass an optional email to handle a user account that's already created. 
    '''
    
    org_email_username = forms.CharField(max_length=200,required=False)
    orgsub_email_domain = forms.CharField(required=False,widget=forms.Select(choices=ORGSUB_EMAILS))
    
    def __init__(self, *args, **kwargs):
        super(OrgSubMemberRegisterForm, self).__init__(*args, **kwargs)
    
    def clean_orgsub_email_domain(self):
        # we want to make sure we don't get RhizomeUser duplicates, 
        # so see if one exists with this orgsub email.        
        org_email_username = self.cleaned_data.get("org_email_username")
        orgsub_email_domain =  self.cleaned_data.get("orgsub_email_domain")
        submitted_email = org_email_username + orgsub_email_domain
        
        try:
            user_check = User.objects.filter(email = submitted_email)
        except:
            user_check = False

        if user_check:
            raise forms.ValidationError(_("This email address is already in use. Please supply a different email address."))
                
        return orgsub_email_domain     
    
    def save(self, *args, **kwargs):
        org_email_username = self.cleaned_data.get("org_email_username")
        orgsub_email_domain = self.cleaned_data.get("orgsub_email_domain")
        submitted_email = org_email_username + orgsub_email_domain
        
        try:
            prospective_user_check = ProspectiveUser.objects.get(email = submitted_email)
        except:
            prospective_user_check = False
            
        if not prospective_user_check:
            # prospective user doesn't exist, so create it
            prospective_user = ProspectiveUser(email = submitted_email)
            prospective_user.registration_code = make_random_string()
            prospective_user.last_invitation = datetime.datetime.now()
            org_sub = Organization.objects.get(email_domain__contains = orgsub_email_domain) 
            prospective_user.org_sub = org_sub
            prospective_user.accepted = 0
            send_invitation_to_member_via_register(submitted_email,prospective_user_check.registration_code)
            send_invitation_to_member_via_register(submitted_email,invite_url)
            prospective_user.save()
            return prospective_user
        else:
            # prospective user exists, but since rhizomeuser 
            # doesn't exist (see cleaning method above) we resend offer 
            prospective_user_check.registration_code = make_random_string()
            prospective_user_check.last_invitation = datetime.datetime.now()
            org_sub = Organization.objects.get(email_domain__contains = orgsub_email_domain) 
            prospective_user_check.org_sub = org_sub
            prospective_user_check.accepted = 0
            send_invitation_to_member_via_register(submitted_email,prospective_user_check.registration_code)
            prospective_user_check.save()
            return prospective_user_check

class OrganizationAdminForm(forms.ModelForm):
    '''
    For validating ip cidr ranges
    '''
    class Meta:
        model = Organization

    def clean_ip_networks(self):
        ip_networks = self.cleaned_data["ip_networks"]
        ip_networks = ip_networks.replace(" ", "").replace("\r\n","")
        ip_networks_as_list = [cidr for cidr in ip_networks.split("," )]
        cleaned_networks_list = []
        for cidr in ip_networks_as_list:
            if cidr:
                if cidr != ",":
                    try:  
                        cidr_as_glob = cidr_to_glob("%s" % cidr)
                        if valid_glob(cidr_as_glob):
                            cleaned_networks_list.append(cidr)
                        else:
                            raise forms.ValidationError(_("%s is not a valid ip range." % cidr))
                    except:
                        raise forms.ValidationError(_("%s is not a valid ip range." % cidr))
                else: 
                    pass
        return ','.join(cleaned_networks_list)

