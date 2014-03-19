from django.core.management.base import BaseCommand, CommandError
from announce.models import Job, Opportunity, Event
from itertools import chain
import datetime
from django.contrib.auth.models import User

class Command(BaseCommand):
    """
    Goes through all announcements and replaces null values for new fields
    """
    def handle(self, *args, **options):
                
        jobs = Job.objects.all()
        events = Event.objects.all()
        opportunities = Opportunity.objects.all()
        
        default_user = User.objects.get(id = 2)
        
        for a in jobs:
            a.is_spam = 0
            a.awaiting_moderation = 0
            if not a.deadline:
                a.deadline = a.created
            try:
                a.save()
            except User.DoesNotExist:  
                a.user = default_user
                a.save()

        for a in events:
            a.is_spam = 0
            a.awaiting_moderation = 0
            if not a.end_date:
                a.end_date = a.created
            
            try:
                a.save()
            except User.DoesNotExist:  
                a.user = default_user
                a.save()
              
        for a in opportunities:
            a.is_spam = 0
            a.awaiting_moderation = 0
            if not a.deadline:
                a.deadline = a.created
            try:
                a.save()
            except User.DoesNotExist:  
                a.user = default_user
                a.save()