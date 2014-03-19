import os
import simplejson as json
import datetime
from django.conf import settings
from artbase.models import Artwork, ArtworkStub
from django.core.management.base import BaseCommand

import logging

#couchdb
from couchdb.client import *
from couchdb.mapping import *
from utils.model_document import ModelDocument
server = Server(settings.COUCH_SERVER)

logger = logging.getLogger('django')

try:
    db = server['artbase']
except Exception:
    try:
        db = server.create('artbase')
    except Exception:
        db = None
        logger.error('Could not access or create artbase CouchDB database')

class Command(BaseCommand):
    '''
    cron daemon will send email stack trace of error if this fails. 
    getting "incomplete read" errors that need to be addressed.
    '''
    help = "Syncs the Artbase CouchDB database, creating any missing views."
    def handle(self, *args, **options):
        print "Sync'ing Artbase"
        if db:
            #Artwork.by_tag.sync(db) #create missing views
            self.update_and_sync_couch()            
            #compact the db 
            db.compact()
        else:
            print "no connection established"
                
    def update_and_sync_couch(self):
        '''
        nightly cron to ensure that couchdb and mysql contain the same data. 
        where fields overlap between mysql and couch, mysql is given       
        primacy as, since the new launch, it contains most of the current information 
        about the work. this is largely due to the fact 
        that we have mysql  so ingrained to django itself
        '''
        #last_twenty_four_hours = datetime.datetime.now() - datetime.timedelta(1)
        artworks = ArtworkStub.objects.all()
        for work in artworks:
            work.sync_document()
