import re

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.forms import ModelForm
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from pychimp import PyChimp

from accounts.models import *
from orgsubs.forms import send_invitation_to_member_via_register, ORGSUB_LIST
from orgsubs.models import Organization
from support.forms import donation_select_amounts 
from utils.helpers import make_random_string

# miniprofilechoices = MiniProfileChoice.objects.all()
# MINIPROFILECHOICES = []
# for choice in miniprofilechoices:
#     MINIPROFILECHOICES.append((choice.id, choice.description))
    
########################################################################


class RhizomeUserChangeForm(UserChangeForm):
    
    class Meta:
        model = RhizomeUser

    def __init__(self, *args, **kwargs):
        super(RhizomeUserChangeForm, self).__init__(*args, **kwargs)
        f = self.fields.get('user_permissions', None)
        if f is not None:
            f.queryset = f.queryset.select_related('content_type')

class RhizomeUserAuthenticationForm(forms.Form):
    """
    COPIED FROM CONTRIB, ALLOWS LONGER USERNAMES FOR ALLOWING EMAILS
    
    Base class for authenticating users. Extend this to get a form that accepts
    username/password logins.
    """
    username = forms.CharField(label=_("Username/Email Address"), max_length=100, widget=forms.TextInput(attrs={'placeholder': 'USERNAME/EMAIL'}))
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput(attrs={'placeholder': 'PASSWORD'}))

    def __init__(self, request=None, *args, **kwargs):
        """
        If request is passed in, the form will validate that cookies are
        enabled. Note that the request (a HttpRequest object) must have set a
        cookie with the key TEST_COOKIE_NAME and value TEST_COOKIE_VALUE before
        running this validation.
        """
        self.request = request
        self.user_cache = None
        super(RhizomeUserAuthenticationForm, self).__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(_("Please enter a correct username and password." + 
                    "Note that both fields are case-sensitive."))
            elif not self.user_cache.is_active:
                raise forms.ValidationError(_("This account is inactive."))

        # TODO: determine whether this should move to its own method.
        if self.request:
            if not self.request.session.test_cookie_worked():
                raise forms.ValidationError(_("Your Web browser doesn't appear to have cookies enabled." +
                    "Cookies are required for logging in."))

        return self.cleaned_data

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache


################################ USER ICON WIDGET USED IN EDIT PROFILE PAGE

class UserIconWidget(forms.FileInput):
    """
    A file upload widget that shows the current icon of the user 
    """
    def __init__(self, attrs={}):
        super(UserIconWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        output = []

        if value and hasattr(value, "url"):
            output.append('<img src = "'+settings.MEDIA_URL+'%s" />' % value )
            if "rhizome_user_default.png" not in value.url:
                output.append('<div class = "edit-profile-form-input"> \
                        <input type="checkbox" name="delete_icon" id="id_delete_icon" /> \
                        <label>Delete this icon?</label></div>')
            if not value:
                output.append('<br /><label>Change your icon? (50px x 50px)</label>')
            else:
                output.append('<br /><label>Select an image (50px x 50px)</label>')
            output.append(super(UserIconWidget, self).render(name, value, attrs))
        else:   
            output.append('<label>Select an image (50px x 50px)</label>')
            
        return mark_safe(u''.join(output))

################################ SMALL FORMS USED IN EDIT PROFILE PAGE

#### EDIT USER FORM
class EditRhizomeUserForm(ModelForm):
    class Meta:
        model = RhizomeUser
        exclude = ('user_id', 'is_staff','is_superuser','is_active','last_login', 
                   'date_joined', 'modified', 'groups', 'user_permissions','password')

    def __init__(self, *args, **kwargs):
        super(EditRhizomeUserForm, self).__init__(*args, **kwargs)


#### PERSONAL INFO FORM

class EditPersonalInfoForm(ModelForm):
    username = forms.CharField(label=_("USERNAME**"))
    
    class Meta:
        model = RhizomeUser
        fields = ('username','url','first_name','last_name','facebook','twitter','email')

    def __init__(self, *args, **kwargs):
        super(EditPersonalInfoForm, self).__init__(*args, **kwargs)
        
    def save(self, *args, **kwargs):
        RhizomeUser = super(self.__class__, self).save(*args, **kwargs)
        return RhizomeUser

#### ACCOUNT/PROFILE INFO FORM

class EditAccountInfoForm(ModelForm):
    visible = forms.BooleanField(label=_("MAKE YOUR PROFILE VISIBLE?"),required=False)
    show_email = forms.BooleanField(label=_("SHOW YOUR EMAIL ADDRESS IN YOUR PROFILE?"),required=False)
    icon = forms.ImageField(required=False, label=_("Icon"),widget=UserIconWidget)
    delete_icon = forms.BooleanField(required=False)
    
    #miniprofile_choices = forms.MultipleChoiceField(choices=MINIPROFILECHOICES,
        #widget=forms.CheckboxSelectMultiple(),required=False,
        #label=_("WHAT WOULD YOU LIKE YOUR MINI-PROFILE TO SHOW?"))
    
    class Meta:
        model = RhizomeUser
#        fields = ('visible','miniprofile_choices','show_email','icon',)
        fields = ('visible','show_email','icon',)

       
    def __init__(self, *args, **kwargs):
        super(EditAccountInfoForm, self).__init__(*args, **kwargs)
        
    def save(self, *args, **kwargs):
        RhizomeUser = super(self.__class__, self).save(*args, **kwargs)
        import os
        if not RhizomeUser.icon or not os.path.exists(RhizomeUser.icon.path):
            RhizomeUser.icon = "accounts/images/icons/rhizome_user_default.png"
        if self.cleaned_data.get('delete_icon'):
            if os.path.exists(RhizomeUser.icon.path):
                if "rhizome_user_default.png" not in RhizomeUser.icon:
                    os.remove(RhizomeUser.icon.path)
            RhizomeUser.icon = 'accounts/images/icons/rhizome_user_default.png'
        RhizomeUser.save()
        return RhizomeUser

#### BIO FORM

class EditBioForm(ModelForm):
    class Meta:
        model = RhizomeUser
        fields = ('bio',)
        
    def __init__(self, *args, **kwargs):
        super(EditBioForm, self).__init__(*args, **kwargs)

#### ADDITIONAL INFO FORM

class EditAdditionalInfoForm(ModelForm):
    class Meta:
        model = RhizomeUser
        fields = ('occupation','industry','education','gender')

    def __init__(self, *args, **kwargs):
        super(EditAdditionalInfoForm, self).__init__(*args, **kwargs)

#### EDIT EMAIL FORM 

class EditEmailForm(ModelForm):
    class Meta:
        model = RhizomeUser

    def __init__(self, *args, **kwargs):
        super(EditEmailForm, self).__init__(*args, **kwargs)
        
################ NEW USER CREATION FORMS

class RhizomeUserCreationForm(UserCreationForm):
    """
    A form that creates a rhizome user, with no privileges, 
    from the given username,email and password.
    """
    username = forms.RegexField(label=_("Create a Username"), max_length=30, regex=r'^\w+$',
        help_text = _("Required. 30 characters or fewer. Alphanumeric characters only (letters, digits and underscores)."),
        error_message = _("This value must contain only letters, numbers and underscores."))
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password Again"), widget=forms.PasswordInput)
    email = forms.EmailField(label=_("Email"),required=True)
    agree_to_terms = forms.BooleanField(label=_("I agree to the terms described above."))
    # honeypot field
    double_verify = forms.CharField(label="Leave this blank", widget=forms.TextInput(attrs={'style': 'display: none;'}), required=False)

    class Meta:
        model = RhizomeUser
        fields = ("username","email")

    def clean_email(self):
        email = self.cleaned_data.get('email').replace(" ","")
        username = self.cleaned_data.get('username')
        if email and RhizomeUser.objects.filter(email=email).exclude(username=username).count():
            raise forms.ValidationError(_("This email address is already in use. Please supply a different email address."))  
        return email        

    def clean_double_verify(self):
        # anti-spam 
        double_verify = self.cleaned_data.get('double_verify')
        if double_verify:
            raise forms.ValidationError('This field must be empty')
        return double_verify
    
    def save(self, commit=True):
        user = super(RhizomeUserCreationForm, self).save(commit=False)
        user.registration_code = make_random_string()
        user.is_active = 0
        user.set_password(self.clean_password2())
        user.email = self.cleaned_data.get('email')
        user.icon = "accounts/images/icons/rhizome_user_default.png"
        if commit:
            user.save()
        return user 

##### REGISTRATION FORM USED ON REGISTER PAGE

class RegistrationUserCreationForm(RhizomeUserCreationForm):
    organization = forms.CharField(required=False, widget=forms.Select(choices=ORGSUB_LIST))
    spam_question = forms.CharField(required=True, label='What will you do with your new Rhizome account?')
    select_amount = forms.DecimalField(label='Select your donation amount', max_digits=15, decimal_places=2, required=False, widget=forms.Select(choices=donation_select_amounts()))
    custom_amount = forms.DecimalField(label='Or enter your own amount', max_digits=15, decimal_places=2, required=False)
    amount = forms.DecimalField(max_digits=15, decimal_places=2, required=False, widget=forms.HiddenInput())

    def clean_organization(self):
        if self.cleaned_data.get('organization') and self.cleaned_data.get('email'):
            org_id = self.cleaned_data['organization']
            organization = Organization.objects.get(id = org_id)
            org_email_domain_list = organization.get_email_domain_list()
            user_email_ending = self.cleaned_data.get('email').split('@')[-1]
            
            for email_domain in org_email_domain_list:
                org_email_ending = email_domain.split('@')[-1]
                org_email_regex = r'%s' % org_email_ending.replace('*', '(.*)')
                match = re.search(org_email_regex, user_email_ending)
                if match:                      
                    return org_id
            raise forms.ValidationError('Your email address does not match that organization.')

    def save(self, commit=False):
        user = super(RegistrationUserCreationForm, self).save(commit=False)
               
        if commit:
            user.spam_question = self.cleaned_data.get('spam_question')

            if self.cleaned_data['organization']:
                # user has orgsub
                org_id = self.cleaned_data['organization']
                organization = Organization.objects.get(id=org_id)
                user.save()
                user.make_orgsub_member(organization)
                send_invitation_to_member_via_register(user.email, user.get_profile().registration_code)
            else:
                user.save()

        return user 

####### BILLING ADDRESS FORM
 
class UserBillingAddressForm(ModelForm):
    billing_locality_province = forms.CharField(required = False)
    
    class Meta:
        model = UserAddress
        exclude = ('user','address_type')
    
    def __init__(self, *args, **kwargs):
        super(UserBillingAddressForm, self).__init__(*args, **kwargs)

    def save(self, user, commit=True):
        address = super(UserBillingAddressForm, self).save(commit=False)
        address.address_type = 'billing'
        address.user = user
        address.save()   
        return address
        
######## SHIPPING ADDRESS FORM

            
class UserShippingAddressForm(ModelForm):
    locality_province = forms.CharField(required = False)
    
    class Meta:
        model = UserAddress
        exclude = ('user','address_type')
        
    def __init__(self, *args, **kwargs):
        super(UserShippingAddressForm, self).__init__(*args, **kwargs)
        
    def save(self, user, commit=True):
        address = super(UserShippingAddressForm, self).save(commit=False)
        address.address_type = 'shipping'
        address.user = user
        address.save()          
        return address

######## MailChimp List Management Form 
        
class ManageMailchimpSubscriptionForm(forms.Form):
    announce_subscribe_checkbox = forms.BooleanField(required=False)
    announce_mailchimp_list = forms.CharField(widget = forms.HiddenInput)
    announce_subscribed_status = forms.BooleanField(widget = forms.HiddenInput, required=False)

    news_subscribe_checkbox = forms.BooleanField(required=False)
    news_mailchimp_list = forms.CharField(widget = forms.HiddenInput)
    news_subscribed_status = forms.BooleanField(widget = forms.HiddenInput, required=False)

    def __init__(self, request, *args, **kwargs):
        super(ManageMailchimpSubscriptionForm, self).__init__(*args, **kwargs)

        #connect to mailchimp to set up form using their info about our lists 
        mailchimp_api = PyChimp('3cb8530ce9770dc992d48f579b6bb09a-us1') 
        mchimp_lists = mailchimp_api.lists()  

        announce_subscribed_status = False
        news_subscribed_status = False
        announce_form_label = ''

        for mchimp_list in mchimp_lists:

            if request.user.get_profile().is_rhizomemember() and mchimp_list["name"] == "Rhizome Members Announcements":
                announce_form_label = mchimp_list["name"] 
                user_info = mailchimp_api.listMemberInfo(mchimp_list["id"], request.user.email)
                if user_info.get("status"):
                    if user_info.get("status") == "subscribed":
                        announce_subscribed_status = True
            
            if not request.user.get_profile().is_rhizomemember() and mchimp_list["name"] == "Rhizome Users Announcements":
                announce_form_label = mchimp_list["name"]                 
                user_info = mailchimp_api.listMemberInfo(mchimp_list["id"], request.user.email)
                if user_info.get("status"):
                    if user_info.get("status") == "subscribed":
                        announce_subscribed_status = True
                    
            if mchimp_list["name"] == "Rhizome News":
                news_form_label = mchimp_list["name"]                 
                user_info = mailchimp_api.listMemberInfo(mchimp_list["id"], request.user.email)
                if user_info.get("status"):
                    if user_info.get("status") == "subscribed":
                        news_subscribed_status = True
                    
        self.fields['announce_subscribe_checkbox'].label = announce_form_label
        self.fields['announce_subscribe_checkbox'].initial = announce_subscribed_status
        self.fields['announce_mailchimp_list'].initial = announce_form_label
        self.fields['announce_subscribed_status'].initial = announce_subscribed_status

        self.fields['news_subscribe_checkbox'].label = news_form_label
        self.fields['news_subscribe_checkbox'].initial = news_subscribed_status
        self.fields['news_mailchimp_list'].initial = news_form_label
        self.fields['news_subscribed_status'].initial = news_subscribed_status
