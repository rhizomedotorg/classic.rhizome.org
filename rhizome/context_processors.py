import os
from orgsubs.models import check_request_for_orgsub
from support.models import CommunityCampaign


def current_campaign(request):
    return {
        'current_campaign': CommunityCampaign.objects.current(),
    }

def check_orgsub(request):
    request_orgsub, is_orgsub_ip, is_orgsub_member = check_request_for_orgsub(request)

    return {
        'request_orgsub': request_orgsub,
        'is_orgsub_ip': is_orgsub_ip,
        'is_orgsub_member': is_orgsub_member,
    }

def first_visit(request):
    if request.session.get('visited', False):
        return {'first_visit': False}
    else:
        request.session['visited'] = True
        return {'first_visit': True}