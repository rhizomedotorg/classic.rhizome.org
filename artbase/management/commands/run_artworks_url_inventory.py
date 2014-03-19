import urllib2
import httplib
import socket
from urllib2 import Request, urlopen, URLError
import csv
import datetime
import os

from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core import mail
from django.conf import settings
from django.core.mail import EmailMessage
from django.db.utils import IntegrityError

from artbase.models import ArtworkStub


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (make_option('--archived',
        action='store_true',
        dest='archived',
        default=False,
        help='only inventory archived works'),
    )
   
    def handle(self, *args, **options):
        '''
        - checks artbase artwork urls.
        - updates needs repair field
        - creates a csv file compiling the http status of broken artbase artworks and their urls and locations
        - sends email to artbase group email with link to csv file
        -takes optional --archived argument to only inventory cloned works
        
        '''
        
        archived = options.get('archived')
        self.run_report_and_create_csv(archived)
        self.send_report_email()
    
    
    def run_report_and_create_csv(self,archived):
        '''
        creates work and report    
        '''
        if archived:
            writer = csv.writer(open(os.path.join(settings.MEDIA_ROOT, "artbase/data/archived_broken_urls_inventory.csv"), "wb"))
        else:
            writer = csv.writer(open(os.path.join(settings.MEDIA_ROOT, "artbase/data/artbase_broken_urls_inventory.csv"), "wb"))        
        writer.writerow(['ARTWORK ID', 'ARTWORK TITLE', 'ARTWORK URL', 'URL STATUS', 'LOCATION', 'LOCATION STATUS','UPDATE NOTICE']) 
        if archived:
            all_works = ArtworkStub.objects.filter(status="approved").filter(location_type="cloned")        
        else:    
            all_works = ArtworkStub.objects.filter(status="approved")

        handler = urllib2.UnknownHandler()
        opener = urllib2.build_opener(handler)
        urllib2.install_opener(opener)    
        
        # timeout in seconds
        timeout = 15
        socket.setdefaulttimeout(timeout)
        
        for work in all_works:   
            url_response = None
            url_error_msg = None
            url_status = None
            location_response = None
            location_status = None
            location_error_msg = None
            updating_notice = None
    
            #a few hacks to make sure the url is formatted correctly
            if "/artbase/" in work.url:
                if "http://archive.rhizome.org" not in work.url:
                    if "http://" not in work.url:
                        work.url = "http://archive.rhizome.org%s" % work.url
                        updating_notice = "Make sure has full rhizome archives url (http://archive.rhizome.org/....)"

            if "/artbase/" in work.location:
                if "http://archive.rhizome.org" not in work.location:
                    if "http://" not in work.location:
                        work.location = "http://archive.rhizome.org%s" % work.location
                        updating_notice = "Make sure has full rhizome archives url (http://archive.rhizome.org/....)"
            if "http://" not in work.url:
                work.url = "http://%s" % work.url
                updating_notice = "Make sure has url including 'http://'"

            if "http://" not in work.location:
                work.location = "http://%s" % work.location
                updating_notice = "Make sure has url including 'http://'"
                     
            try:
                url_response = urllib2.urlopen(work.url, timeout = 15)
            except (urllib2.URLError, httplib.BadStatusLine, httplib.InvalidURL, httplib.HTTPException,httplib.UnknownProtocol), e:
                if hasattr(e, 'reason'):
                        if isinstance(e.reason, socket.timeout):
                            url_error_msg = 'Failed to reach server. TIMED OUT '
                        else:
                            url_error_msg = 'Failed to reach server. Reason: %s ' % e.reason
                elif hasattr(e, 'code'):
                    url_error_msg = "The server couldn't fulfill the request. Error code: %s" % e.code
                else:
                    url_error_msg = "Failed to reach server!"                    
            except:
                url_error_msg = "Failed to reach server!"
                  
            if url_response:
                url_status = "SUCCESS"
            else:
                url_status = url_error_msg
            
            
            if work.location:
                try:
                    location_response = urllib2.urlopen(work.location, timeout = 15)
                except (urllib2.URLError, httplib.BadStatusLine, httplib.InvalidURL, httplib.HTTPException,httplib.UnknownProtocol), e:
                    if hasattr(e, 'reason'):
                        if isinstance(e.reason, socket.timeout):
                            url_error_msg = 'Failed to reach server. TIMED OUT '
                        else:
                            location_error_msg = 'Failed to reach a server. Reason: %s ' % e.reason
                    elif hasattr(e, 'code'):
                        location_error_msg = "The server couldn't fulfill the request. Error code: %s" % e.code
                    else:
                        location_error_msg = "Failed to reach server!"
            
            if location_response:
                location_status = "SUCCESS"
            else:
                location_status = location_error_msg
         
            if location_error_msg or url_error_msg and not updating_notice:
                updating_notice = "This work has broken links"                 
            
            if updating_notice:
                work.needs_repair = True
                try:
                    work.save()
                except IntegrityError:
                    pass
                except User.DoesNotExist:  
                    work.user = rhizome_user
                    work.save()
                
                writer.writerow([    
                    "%s" % work.id,
                    "%s" % work.title,
                    "%s" % work.url,
                    "%s" % url_status,
                    "%s" % work.location,
                    "%s" % location_status,
                    "%s" % updating_notice,
                ])
        
        def send_report_email(self):
            report_email = EmailMessage(
                'ArtBase Broken URLs Inventory Report', 
                'Report available here: %s' % (os.path.join(settings.MEDIA_ROOT, "artbase/data/artbase_broken_urls_inventory.csv")), settings.ARTBASE_GROUP_EMAIL, 
                [settings.ARTBASE_GROUP_EMAIL], 
                headers = {'Reply-To': settings.ARTBASE_GROUP_EMAIL})  
            report_email.send()
            
