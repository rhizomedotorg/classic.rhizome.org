from django.core.management.base import BaseCommand, CommandError
from accounts.models import RhizomeUser,RhizomeMembership
from artbase.models import ArtworkStub
from orgsubs.models import Organization
from django.contrib.auth.models import User

class Command(BaseCommand):
    """
    Goes through artbase and adds all artists to rhizome's organizational subscription
    """
    def handle(self, *args, **options):
        artbase_artworks = ArtworkStub.objects.filter(status="approved")     
        rhizome_org_sub = Organization.objects.get(name="Rhizome")
        rhizome_user = RhizomeUser.objects.get(pk=2)
        for work in artbase_artworks:
            try:
                if work.user.get_profile().membership():
                    work.user.get_profile().membership().make_complimentary()
                else:
                    membership = RhizomeMembership(user=work.user) 
                    membership.archival_access = 1
                    membership.member_tools = 1
                    membership.archival_access_exp_date = rhizome_org_sub.expiration_date
                    membership.member_tools_exp_date = rhizome_org_sub.expiration_date
                    membership.org_sub = rhizome_org_sub
                    membership.save()  
            except User.DoesNotExist:  
                work.user = rhizome_user
                work.save()