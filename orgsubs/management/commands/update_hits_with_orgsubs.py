import datetime

from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from netaddr import IPAddress, IPNetwork

from hitcount.models import Hit
from orgsubs.models import Organization

class Command(BaseCommand):
    '''
    updates hit objects with orgsub info. gonna be massive.
    '''

    def handle(m, *args, **options):
        hits = Hit.objects.all().filter(orgsub_ip = None)[:25000]
        #hits = Hit.objects.all().filter(orgsub__pk = 70)

        orgsub_ids_and_networks = [ ( orgsub, orgsub.ip_networks.split("," ) ) for orgsub in \
            Organization.objects.filter(ip_access = True)]
        
        #print '##################'
        #print '######### started at %s' % datetime.datetime.now()
        #print '##################'

        if hits:
            for hit in hits:
                print hit.id
                ip = str(hit.ip)
                is_ip = False
                is_member = False
                request_orgsub = None
                member_orgsub = None

                # if user, check for orgsub
                if hit.user:
                    try:
                        member_orgsub = hit.user.get_profile().orgsub()
                    except ObjectDoesNotExist:
                        #print 'cant find user: %s' % hit.user.id
                        pass
                
                # if orgsub, add it to the hit
                if member_orgsub:
                    is_member = True
                    
                    if not request_orgsub:
                        request_orgsub = member_orgsub
                
                # check to see if ip in an orgsub range
                try:
                    remote_ip = IPAddress("%s" % ip) 
                except:
                    remote_ip = None

                if remote_ip:
                    for orgsub in orgsub_ids_and_networks:    
                        if orgsub[1][0]:
                            networks = orgsub[1]

                            for network in networks:
                                converted_network =  IPNetwork(str(network))
                                if remote_ip in converted_network:
                                    is_ip = True
                                    request_orgsub = orgsub[0]


                hit.orgsub = request_orgsub
                hit.orgsub_ip = is_ip
                hit.orgsub_member = is_member
                hit.save()
        
        #print '##################'
        #print '######### finished at %s' % datetime.datetime.now()
        #print '##################'
