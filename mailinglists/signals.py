import datetime

import django.dispatch
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.comments.signals import comment_was_posted
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.mail import send_mass_mail,send_mail, EmailMultiAlternatives, EmailMessage, BadHeaderError
from django.db.models.signals import post_save, pre_save
from django.template.loader import get_template
from django.template import Context

from accounts.models import RhizomeUser
from threadedcomments.models import *
from utils.helpers import bbcode_to_html


######## FUNCTIONS FOR UPDATING THE LISTS ###########
def update_mailing_list_members_on_rhizomeuser_save(sender, instance, created, **kwargs):
    '''
    updates a user's mailing list email on rhizome user save
    '''
    from models import Member
    
    try:    
        list_member = Member.objects.filter(user = instance.user)   
    except:
        try:
            # check to see if member object with the newly saved email, 
            #if so, attach it to user via the below
            list_member = Member.objects.filter(email = instance.user.email)
        except:
            list_member = None
    
    if list_member:
        for member in list_member:
            #make sure rhizomeuser/member are connected
            member.user = instance.user 
            member.email = instance.user.email
            member.save()

post_save.connect(update_mailing_list_members_on_rhizomeuser_save, sender=RhizomeUser, dispatch_uid ="accounts.rhizomeuser") 

def update_mailing_list_members_on_user_save(sender, instance, created, **kwargs):
    '''
    updates a user's mailing list email on django user save
    '''
    from models import Member
    
    try:    
        list_member = Member.objects.filter(user = instance)   
    except:
        try:
            # check to see if member object with the newly saved email, if so, attach it to user via the below
            list_member = Member.objects.filter(email = instance.user.email)
        except:
            list_member = None
    
    if list_member:
        for member in list_member:
            member.user = instance #make sure rhizomeuser/member are connected
            member.email = instance.email
            member.save()
 
post_save.connect(update_mailing_list_members_on_user_save, sender=User, dispatch_uid ="auth.user")  


############################ FUNCTIONS FOR SENDING EMAILS TO THE LISTS

#############
####### SEND TO DISCUSS LIST
##############
def send_to_discuss_mailing_list(comment, request): 
    """
    Handles sending approved posts to discuss listserv.
    """
    #import models here to prevent circular import problem
    from mailinglists.models import List, MLMessage, Member
    
    if comment.is_public == 1:
        # create a new MLMessage 
        # check to see if already recorded/sent, 
        # if not send and save
        discuss_list = List.objects.get(listemail='discuss@rhizome.org')

        mlmessage = MLMessage()
        mlmessage.user = request.user
        mlmessage.mllist = discuss_list
        mlmessage.content_type = ContentType.objects.get(app_label="discuss", model="discussionthread")
        mlmessage.object_pk = comment.id   
                  
        message_check = MLMessage.objects.filter(object_pk = mlmessage.object_pk, \
            content_type = mlmessage.content_type, \
            mllist = mlmessage.mllist
        )
        
        if not message_check:
            recipients = Member.objects.values('email').filter(listid=discuss_list.id).filter(deleted=0)
            bcc = [i['email'] for i in recipients]
            subject = comment.title

            current_site = Site.objects.get_current()

            d = {
                'comment': comment, 
                'comment_body': comment.comment,
                'comment_url': 'http://%s%s' % (current_site.domain, comment.get_absolute_url())
            }

            plaintext_template = get_template('discuss/email_templates/plaintext.txt') 
            plaintext_message = plaintext_template.render(Context(d))
    
            html_template = get_template('discuss/email_templates/html.html') 
            html_message = html_template.render(Context(d))
            
            email = EmailMultiAlternatives(
                '[Rhizome Discuss] %s' % subject, 
                plaintext_message, 
                'discuss@rhizome.org', 
                ['discuss@rhizome.org'], 
                bcc, 
                headers = {'Reply-To': 'no-reply@rhizome.org'}
            )
            email.attach_alternative(html_message, 'text/html')              

            try:
                email.send(fail_silently=False)
                mlmessage.sent = True
            except:
                mlmessage.sent = False
             
            mlmessage.save()
                    
#############
####### SEND TO ANNOUNCE LIST
##############

'''
Email sending is broken up into 1 main function that creates the email 
and then passes it off to functions that send it to diff't lists. 
'''

#FUNCTION FOR CREATING THE EMAIL AND HANDING IT TO BE SENT TO LISTS

# DOES CREATED NEED TO BE SENT?

def send_to_announce_mailing_list(sender, instance, created):
        
    if created == True:
        current_site = Site.objects.get_current()
       
        plaintext_content = {
            "announcement":instance, 
            "announcement_body":instance.description_strip_bbcode(),
            "current_site":current_site
        }
        
        plaintext_template = get_template('announce/email_templates/announcement.txt')
        plaintext_message = plaintext_template.render(Context(plaintext_content))

        html_content = {
            "announcement":instance, 
            "announcement_body":bbcode_to_html(instance.description),
            "current_site":current_site,
        }
        
        html_template = get_template('announce/email_templates/announcement.html')
        html_message = html_template.render(Context(html_content))

        email_subject = "[Rhizome Announce] %s" % instance.title
        
        instance_email = EmailMultiAlternatives(email_subject, 
            plaintext_message, 'announce@rhizome.org', 
            ['announce@rhizome.org'], 
            headers = {'Reply-To': 'no-reply@rhizome.org'
        })
        
        #send html version as well
        instance_email.attach_alternative(html_message, "text/html")

        sub_content_type = ContentType.objects.get_for_model(instance)
        
        # hand off messages to be sent to diff't lists
        # import models here to prevent circular import problem
        from models import List, MLMessage, Member 
        send_to_announce_main(instance, created, instance_email, sub_content_type)
        send_to_announce_sub(instance, created, instance_email, sub_content_type)

#SEND EMAIL TO MAIN ANNOUNCEMENT LIST and Track it with MLMessage instance    
def send_to_announce_main(instance, created, instance_email, sub_content_type):
    from models import List, MLMessage, Member #import models here to prevent circular import problem
    
    #check to see if already recorded/sent, if not send
    announce_main_list = List.objects.get(listemail='announce@rhizome.org')

    message_check = MLMessage.objects.filter(
        object_pk = instance.id, 
        content_type = instance.content_type, 
        mllist = announce_main_list
    )

    if not message_check:
        #create the bcc recipient list and add it to the email    
        announce_main_members = Member.objects.values('email').filter(listid = announce_main_list.id).exclude(deleted = 1)
        announce_main_recipients_list = [ i['email'] for i in announce_main_members]
        instance_email.bcc = announce_main_recipients_list
    
        #create the mlmessage
        main_mlmessage = MLMessage()
        main_mlmessage.user = instance.user
        main_mlmessage.mllist = announce_main_list
        main_mlmessage.content_type = sub_content_type
        main_mlmessage.object_pk = instance.id
            
        # send
        try:
            instance_email.send(fail_silently=False)
            main_mlmessage.sent = True
        except:
            main_mlmessage.sent = False
        main_mlmessage.save()
        
    else:
        pass
        #print 'announce message already sent'
        
#SEND announce sub lists and Track it with MLMessage instance    
def send_to_announce_sub(instance, created, instance_email, sub_content_type):
    from models import List, MLMessage, Member 
    
    #create the bcc recipient list and add it to the email    
    announce_sub_list = List.objects.get(content_type=sub_content_type)

    #check to see if already recorded/sent, if not send
    message_check = MLMessage.objects.filter(
        object_pk = instance.id, 
        content_type = instance.content_type, 
        mllist = announce_sub_list
    )


    if not message_check:
        announce_sub_list_members = Member.objects.values('email').filter(listid = announce_sub_list.id).exclude(deleted = 1)
        announce_sub_recipient_list = [i['email'] for i in announce_sub_list_members]
        instance_email.bcc = announce_sub_recipient_list
        instance_email.subject = "[%s] %s" % (announce_sub_list.title, instance.title)
    
        #create the mlmessage
        sub_mlmessage = MLMessage()
        sub_mlmessage.user = instance.user
        sub_mlmessage.mllist = announce_sub_list
        sub_mlmessage.content_type = sub_content_type
        sub_mlmessage.object_pk = instance.id 
        
        try:
            instance_email.send(fail_silently=False)
            sub_mlmessage.sent = True
        except:
            sub_mlmessage.sent = False
        
        sub_mlmessage.save()
    else:
        #print 'message already sent'
        pass