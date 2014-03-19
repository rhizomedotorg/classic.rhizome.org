from django.db import models
from django.contrib.auth.models import User
import datetime
from countries.models import Country, UsState
from itertools import chain
import re
from netaddr import IPAddress, IPNetwork, valid_nmap_range,valid_ipv6,cidr_to_glob

class Organization(models.Model):
    name = models.CharField(max_length=255, null=False,db_index = True)
    short_name = models.CharField(max_length=50, null=True, blank=True)
    size = models.IntegerField(max_length=11, null=False)
    description =  models.TextField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    donation_required = models.FloatField(null=True)
    expiration_date = models.DateTimeField(null=False,db_index = True)
    last_alert_sent = models.DateTimeField(null=True,blank=True)
    ip_access = models.BooleanField(db_index = True)
    ip_networks = models.TextField(null=True, blank=True, help_text="<b style = 'color:black;'-Multiple network ranges must be separated by commas.<br />-Network ranges must be in <a href='http://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing'>CIDR</a> format, eg 64.20.128.0/24.<br />-Individual ip's are accepted.<br />-Use this tool to check ip range to cidr conversion: <a href='http://ip2cidr.com/'>http://ip2cidr.com/</a></b>")
    created = models.DateTimeField(null=False, editable=False)
    modified = models.DateTimeField(null=False, editable=False, auto_now=True)
    active = models.BooleanField(blank=True)
    cancelled = models.BooleanField(blank=True)
    complimentary = models.BooleanField()
    uri = models.CharField(max_length=256, null=True,help_text="Full url, including http://")
    publicize_email = models.NullBooleanField()
    street1 = models.CharField(max_length=50, null=True, blank=True)
    street2 = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(null=False, blank=True, max_length=255,db_index = True)
    state = models.ForeignKey(UsState,to_field='name',null=True, blank=True)
    locality_province = models.CharField(max_length=100, null=True, blank=True)
    zip_postal_code = models.IntegerField(max_length=10, null=True, blank=True)
    country = models.ForeignKey(Country,null=True, blank=True)
    publicize_location = models.NullBooleanField()
    test_group = models.NullBooleanField(db_index = True)
    auto_add_email_subscription = models.NullBooleanField(help_text="Automatically add users have org's email_domain?")
    email_access = models.NullBooleanField(help_text="Does this group allow email access?", db_index = True)
    email_domain = models.TextField(null=True)
    rhiz_admin_contact_info = models.TextField(null=True)
    general_contact_info = models.TextField(null=False)
    billing_contact_info = models.TextField(null=False)
    notes = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return '%s' % (self.name)
        
    class Meta:
        ordering = ('name',)

    def expired(self):
        return not self.active
    
    def get_admins(self):
        from accounts.models import RhizomeMembership 
        admins = []
        for admin in RhizomeMembership.objects.filter(org_sub = self.id).filter(org_sub_admin = True):
            admins.append(admin.user)    
        return admins
    
    def get_ip_networks(self):
        #returns ip ranges with <br /> instead of comma, used in presentation
        ip_networks = self.ip_networks
        ip_networks = ip_networks.replace(",", "<br />")
        return ip_networks
        
    def get_email_domain(self):
        #returns email domain with <br /> instead of comma, used in presentation
        email_domain = self.email_domain
        email_domain = email_domain.replace(",", "<br />")
        return email_domain

    def get_email_domain_list(self):
        #returns email domain as a list
        return [x for x in self.email_domain.split(",")]
        
    def get_member_count(self):
        from accounts.models import RhizomeMembership 
        member_count = RhizomeMembership.objects.filter(org_sub = self).count()
        return member_count
        
    get_member_count.short_description = 'Member Count'
        
    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = datetime.datetime.now()
        self.modified = datetime.datetime.now()
        if self.ip_networks:
            self.ip_access = True
        if self.email_domain:
            self.ip_access = True
        if self.expiration_date < datetime.datetime.now():
            self.expired = True
        if self.expiration_date > datetime.datetime.now():
            self.expired = False
        super(Organization, self).save(*args, **kwargs)

class MonthlyStatistics(models.Model):
    org_sub = models.ForeignKey(Organization)
    year_month = models.DateField(null=False)
    total_visits = models.IntegerField(max_length=15)
    ip_visits = models.IntegerField(max_length=15)
    member_visits = models.IntegerField(max_length=15)

    class Meta:
        unique_together = (("org_sub", "year_month"),)

    def __unicode__(self):
        return '%s for %s' % (self.org_sub, self.year_month)
    
    def save(self, *args, **kwargs):
        super(MonthlyStatistics, self).save(*args, **kwargs)

    
class Payment(models.Model):
    org_sub = models.ForeignKey(Organization)
    amount = models.FloatField()
    payment_type = models.CharField(max_length=256, null=True)
    date = models.DateTimeField(null=False)
    
    def __unicode__(self):
        return '%s on %s' % (self.org_sub, self.date)
    
    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.date = datetime.datetime.now()
        super(Payment, self).save(*args, **kwargs)
    
class Invoice(models.Model):
    org_sub = models.ForeignKey(Organization)
    amount = models.FloatField()
    payment_type = models.CharField(max_length=256, null=True)
    date = models.DateTimeField(null=True,)
    
    def __unicode__(self):
        return '%s on %s' % (self.org_sub, self.date)
    
    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.date = datetime.datetime.now()
        super(Invoice, self).save(*args, **kwargs)
    
class ProspectiveUser(models.Model):
    email = models.CharField(max_length=256, null=False)
    org_sub = models.ForeignKey(Organization, null=True)
    user =  models.ForeignKey(User, null=True,blank=True, related_name="the potential user")
    created = models.DateTimeField(null=True)
    last_invitation = models.DateTimeField(null=True)
    invite_admin = models.ForeignKey(User, null=True, related_name="the org sub admin")
    accepted = models.BooleanField()
    registration_code = models.CharField(max_length=25,null=False,blank=True)
    removed = models.BooleanField()
    
    def __unicode__(self):
        return '%s' % (self.email)
    
    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = datetime.datetime.now()
        self.email = self.email.replace(",","").replace(" ","")
        super(ProspectiveUser, self).save(*args, **kwargs)


#####################ORGSUB FUNCTIONS    

def is_ip_org_sub(ip):
    '''
    For organizational subscription access, 
    checks to see if an users IP in within an organizational subscription range, 
    returns True or False
    '''
    #take all ranges and flatten them into one list
    orgsub_ip_ranges_list = [((org_sub_networks["ip_networks"]).split("," )) for org_sub_networks in \
                Organization.objects
                    .filter(ip_access=True)
                    .filter(active = True)
                    .values("ip_networks")
                ]
    ip_ranges_flattened = list(chain.from_iterable(orgsub_ip for orgsub_ip in orgsub_ip_ranges_list)) 
    
    #now check if the ip is in the list of ip_ranges
    access = False
    for ip_range in ip_ranges_flattened:
        try:
            if IPAddress("%s" % ip) in IPNetwork('%s' % ip_range):
                access = True
        except:
            pass
    return access

def check_request_for_orgsub(request):
    '''
    Checks ip range and user info in request, and returns orgsub if available
    '''
    ip = str(request.META['REMOTE_ADDR'])
    is_member = False
    is_ip = False
    request_orgsub = None
    member_orgsub = None

    if ip:
        remote_ip = IPAddress(ip)
        
        if request.user.is_authenticated():
            member_orgsub = request.user.get_profile().orgsub()

        orgsub_ids_and_networks = [ ( orgsub, orgsub.ip_networks.split("," ) ) for orgsub in \
                Organization.objects
                    .filter(ip_access = True)
                    .filter(active=True)
                ]
        
        for orgsub in orgsub_ids_and_networks:    
            # check to make sure it's not actually empty
            if orgsub[1][0]:
                networks = orgsub[1]

                for network in networks:
                    converted_network =  IPNetwork(str(network))
                    if  remote_ip in converted_network:
                        is_ip = True
                        request_orgsub = orgsub[0]

            if member_orgsub:
                is_member = True
                if not request_orgsub:
                    request_orgsub = member_orgsub

    return request_orgsub, is_ip, is_member 

