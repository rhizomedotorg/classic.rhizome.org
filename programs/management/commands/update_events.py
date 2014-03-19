from django.core.management.base import BaseCommand, CommandError
from programs.models import *
import os

class Command(BaseCommand):
    """
    saving creates thumbnails and images for blog posts
    """
    def handle(self, *args, **options):

        events = RhizEvent.objects.all()
        for event in events:
            if event.is_new_silent:
                curator = User.objects.get(pk = 1040981)
                event.curator.add(curator)
            event.save()        
        
#         exhibitions = Exhibition.objects.all()
#         for exhibition in exhibitions:
#             exhibition.save()
        
