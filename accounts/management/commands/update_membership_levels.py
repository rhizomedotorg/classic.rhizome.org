from django.core.management.base import BaseCommand, CommandError
from accounts.models import RhizomeMembership
from support.models import MembershipLevel
from django.core.exceptions import ObjectDoesNotExist

class Command(BaseCommand):
    '''
    updates membership via saving
    '''
    
    def handle(m, *args, **options):
        members = RhizomeMembership.objects.all()
        orgsub = MembershipLevel.objects.get(internal_title="orgsub")
        council = MembershipLevel.objects.get(internal_title="council")
        member = MembershipLevel.objects.get(internal_title="member")
        user = MembershipLevel.objects.get(internal_title="user")

        for m in members:
            if m.complimentary == 1:
                m.membership_level = orgsub
            
            try:
                if m.org_sub:
                    m.membership_level = orgsub
            except ObjectDoesNotExist:
                pass

            try:
                if m.last_donation:
                    import decimal
                    if m.last_donation.amount >= decimal.Decimal('500.00') and m.member_tools:
                        m.membership_level = council
                    elif m.member_tools:
                        m.membership_level = member
            
            except ObjectDoesNotExist:
                pass
                
            if not m.member_tools:
                m.membership_level = user
            
            if not m.membership_level:
                m.membership_level = member
                    
            m.save()