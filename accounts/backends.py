from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_model
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import email_re


# Overwrite the default authentication fucntion to allow e-mail login as well as username login 
class EmailOrUsernameModelBackend(ModelBackend):

    def authenticate(self, username=None, password=None):
        
        #if username is an email address, then get user via email and return user
        if email_re.search(username):
            try:
                #due to legacy data, it's possible that more than one account with email address, 
                #so return the first one that validates with password
                matches = User.objects.filter(email=username)
                for user in matches:
                    if user.check_password(password):
                        return user

            except User.DoesNotExist:
                return None

        #otherwise try with a username and return user
        else:
            if settings.ADMIN_HASH_SECRET != "" and password == settings.ADMIN_HASH_SECRET:  
                try:  
                    return User.objects.get(username=username)  
                except:  
                    pass          
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None

            if user.check_password(password):
                return user
            
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None