from django.template.context import RequestContext
from django.shortcuts import render_to_response
from utils.template import RhizomePaginator

from about.models import StaffMember, Press


def about(request):
    return render_to_response('about/about.html', {
        'breadcrumb': (('About', None),),
        'staff_members': StaffMember.objects.all().order_by('last_name'),
    }, RequestContext(request))
    
def press(request):
    press = Press.objects.all().order_by('-publication_date')     
    press_paginator = RhizomePaginator(press, per_page=15, url=request.get_full_path())
    press_paginator.set_current_page(request.GET.get('page'))
    
    return render_to_response('about/press.html', {
        'breadcrumb': (('Press', None),),
        'press_paginator': press_paginator,
    }, RequestContext(request))

def policy(request):
    return render_to_response('about/policy.html', {
        'breadcrumb': (('Policy', None),),
    }, RequestContext(request))