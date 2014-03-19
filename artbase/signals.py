from accounts.models import RhizomeUser
from django.db.models.signals import post_save, pre_save
from django.utils.html import strip_tags

#SIGNAL FOR STORING USERNAME IN ARTBASE NAMES TABLE
def artbase_addname(sender, *args, **kwargs):
    print "Add a name!"
    pass
post_save.connect(artbase_addname, sender=RhizomeUser)
