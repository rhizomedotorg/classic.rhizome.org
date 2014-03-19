from django.core.management.base import BaseCommand, CommandError
from artbase.models import ArtworkStub
from tagging.models import Tag
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
import datetime

class Command(BaseCommand):
    """
    Just saves all the artworks, use for mass updates
    """
    def handle(self, *args, **options):
        rhizome_user = User.objects.get(pk=2)
        artbase_artworks = ArtworkStub.objects.filter(status = "awaiting")
        cutoff_date = datetime.datetime.now() - datetime.timedelta(125)
        
        for work in artbase_artworks:
            if not work.submitted_date:
                work.submitted_date = work.created
        
            if work.submitted_date <= cutoff_date:
                if not work.is_halfway_complete():
                    work.status = "rejected"

                    try:
                        work.save()
                    except User.DoesNotExist:  
                        work.user = rhizome_user
                        work.save()
                    except IntegrityError:
                        pass