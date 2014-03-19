import datetime

from django import forms
from django.contrib.auth.models import User
from django.template.context import RequestContext
from django.core.mail import send_mass_mail,send_mail, EmailMessage, BadHeaderError
from django.utils.translation import ugettext_lazy as _
from django.forms import ModelForm


from models import *

lists = List.objects.all()
LISTS = []
for mailinglist in lists:
    LISTS.append((mailinglist.id, mailinglist.title))

class SubscribeForm(forms.Form):
    mailinglists = forms.MultipleChoiceField(choices=LISTS, widget=forms.CheckboxSelectMultiple(), required=True, label=_("Check the box to subscribe to that list:"))
    email = forms.EmailField(label=_("Your email address:"), required=True)
    
    def __init__(self, *args, **kwargs):
        super(SubscribeForm, self).__init__(*args, **kwargs)

    def clean_mailinglists(self):
        mailinglists = self.cleaned_data.get('mailinglists')

        if not mailinglists:
            raise forms.ValidationError(_("Please Select A List"))
        return mailinglists

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError(_("Please Enter Your Email Address"))
        return email

    def save(self, request, *args, **kwargs):
        notice = {}
        existing = []
        subscribed = []
        
        sumbitted_email = self.cleaned_data.get("email")
        mailinglists = self.cleaned_data.get("mailinglists")
                
        user = None
        
        #get user acct if available
        if request.user.is_authenticated():
            user = request.user
        else:            
            try:
                users = User.objects.filter(email=sumbitted_email)[:1]
                for u in users:
                    user = u
            except User.DoesNotExist:
                user = None
        
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        
        for mailinglist in mailinglists:
            listobject = List.objects.get(pk = mailinglist)
            deleted_email = sumbitted_email.replace('@','[at]')

            #check to see if previously signed up
            try:
                is_deleted_member =  Member.objects.get(listid=listobject.id, email=deleted_email, deleted=1)
            except Member.DoesNotExist:
                is_deleted_member = None
            
            #check to see if currently signed up
            try:
                is_member = Member.objects.get(listid=listobject.id, email=sumbitted_email, deleted=0)
            except Member.DoesNotExist:
                is_member = None
                
            if is_member:
                existing.append("%s" % listobject.id)
            
            #check to see if previously deleted, if so, reactivate existing account            
            if is_deleted_member:
                #resubscribing
                is_deleted_member.email = sumbitted_email
                is_deleted_member.delete_date = None
                is_deleted_member.deleted = 0
                is_deleted_member.save()
                
                #send email notice
                subject = '%s: Thanks for signing up!' % (listobject.title)
                from_email = '%s' % (listobject.listemail)
                message = 'You have signed up for %s. Please click here to confirm: http://rhizome.org/mailinglists/confirm/%s/?email=%s' % (listobject.title, listobject.id, sumbitted_email)
                to = [sumbitted_email]
                confirm_email = EmailMessage(subject, message, from_email, to, headers = {'Reply-To': 'no-reply@rhizome.org'})
                confirm_email.send(fail_silently=False)
                
                subscribed.append("%s" % listobject.id)
                
            #create record if brand new
            if is_member == None and is_deleted_member == None:
                if user:
                    newmember = Member(user= user, listid=mailinglist, email=sumbitted_email,IP=ip_address)
                else:
                    newmember = Member(listid=mailinglist, email=sumbitted_email,IP=ip_address)
                newmember.save()
                
                #send email notice
                subject = '%s: Thanks for signing up.' % (listobject.title)
                from_email = '%s' % (listobject.listemail)
                message = 'You have signed up for %s. Please click here to confirm: http://rhizome.org/mailinglists/confirm/%s/?email=%s' % (listobject.title,listobject.id, sumbitted_email)
                to = [sumbitted_email]
                confirm_email = EmailMessage(subject, message, from_email, to, headers = {'Reply-To': 'no-reply@rhizome.org'})
                confirm_email.send(fail_silently=False)
                
                subscribed.append("%s" % listobject.id)
            
        
        notice["subscribed"] = subscribed   
        notice["existing"] = existing   
        
        return notice

class UnsubscribeForm(forms.Form):
    mailinglists = forms.MultipleChoiceField(choices=LISTS,widget=forms.CheckboxSelectMultiple(),required=True,label=_("From which lists do you wish to be removed?"))
    email = forms.EmailField()
    
    def __init__(self, *args, **kwargs):
        super(UnsubscribeForm, self).__init__(*args, **kwargs)

    def clean_list(self):
        mailinglists = self.cleaned_data.get('mailinglist')
        if not mailinglists:
            raise forms.ValidationError(_("Please Select A List"))
        return mailinglists

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError(_("Please Enter Your Email Address"))
        return email

    def save(self, request, *args, **kwargs):
        notice = ''
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        sumbitted_email = self.cleaned_data["email"]
        mailinglists = self.cleaned_data["mailinglists"]
        notice = {}
        notsubscribed = []
        unsubscribed = []
        
        for mailinglist in mailinglists:
            listobject = List.objects.get(pk=mailinglist)
            is_member = False

            # verify member of list
            try:
                is_member = Member.objects.get(listid=listobject.id, email=sumbitted_email, deleted=0)
            except:
                pass
                
            if is_member:
                is_member.deleted = 1
                is_member.delete_date = datetime.datetime.now()
                is_member.email = is_member.email.replace('@','[at]')
                is_member.save()
                
                subject = '%s: You have been unsubscribed' % (listobject.title)
                from_email = '%s' % (listobject.listemail)
                message = '%s has been been unsubscribed from %s' % (sumbitted_email, listobject.title)
                to = [sumbitted_email]
                confirm_email = EmailMessage(subject, message, from_email, to, headers = {'Reply-To': 'no-reply@rhizome.org'})
                confirm_email.send(fail_silently=False)
                
                unsubscribed.append("%s" % listobject.id)
            else:
                notsubscribed.append("%s" % listobject.id)
        
        notice["unsubscribed"] = unsubscribed   
        notice["notsubscribed"] = notsubscribed   
        
        return notice
        
class ManageForm(forms.Form):
    mailinglists = forms.MultipleChoiceField(choices=LISTS,required=False,widget=forms.CheckboxSelectMultiple())
    
    def save(self, request, mailinglists):
        notice = ''
        user = request.user
        email = user.email
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        mailing_lists = List.objects.all()
        
        if not mailinglists:
            for ml in mailing_lists:
                member = ''
                try:
                    member = Member.objects.get(listid=ml.id, email=email, deleted=0)
                except:
                    pass
                if member:
                    member.deleted = 1
                    member.delete_date = datetime.datetime.now()
                    member.email = member.email.replace('@','[at]')
                    member.save()
                    notice = notice + '%s has been been unsubscribed from %s<br/>' % (user.email,ml.title)
                else:
                    notice = notice + "%s is not subscribed to %s<br/>" % (user.email,ml.title)
            return notice
        else:            
            '''
            kinda hacky, delete them first then...
            '''
            for ml in mailing_lists:
                try:
                    member = Member.objects.get(listid=ml.id, email=email, deleted=0)
                except Member.DoesNotExist:
                    member = None
                if member:
                    member.deleted = 1
                    member.email = member.email.replace('@','[at]')
                    member.save()
                                                 
                for mailinglist in mailinglists:
                    '''
                    ...sign them back up or create new member
                    '''
                    listobject = List.objects.get(pk=mailinglist)
                    if ml == listobject:
                        deleted_email = request.user.email.replace('@','[at]')
                        try:
                            is_deleted_member =  Member.objects.get(listid=listobject.id, email=deleted_email, deleted=1)
                        except Member.DoesNotExist:
                            is_deleted_member = None
                                                
                        if is_deleted_member != None:
                            is_deleted_member.email = request.user.email
                            is_deleted_member.delete_date = None
                            is_deleted_member.deleted = 0
                            is_deleted_member.save()
                            
                        try:
                            is_member = Member.objects.get(listid=listobject.id,email=email,deleted=0)
                        except Member.DoesNotExist:
                            is_member = None
                        
                        if is_member == None and is_deleted_member == None:
                            newmember = Member(user_id=user.id, listid=mailinglist, email=email,IP=ip_address,)
                            newmember.save()
                            subject = '%s: Thanks for signing up!' % (listobject.title)
                            from_email = '%s' % (listobject.listemail)
                            message = 'You have signed up for %s. Please click here to confirm: http://rhizome.org/mailinglists/confirm/%s/?email=%s' % (listobject.title, listobject.id, user.email)
                            to = [user.email]
                            confirm_email = EmailMessage(subject, message, from_email, to, headers = {'Reply-To': 'no-reply@rhizome.org'})
                            confirm_email.send(fail_silently=False)
