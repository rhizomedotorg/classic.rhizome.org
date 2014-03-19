#http://joshuajonah.ca/blog/2010/06/18/poor-mans-esi-nginx-ssis-and-django/
#http://ericholscher.com/blog/2010/aug/22/lessons-learned-dash-ghetto-nginx-ssi/

import re
from django.core.urlresolvers import get_urlconf, get_resolver, Resolver404

from netaddr import IPAddress

from orgsubs.models import is_ip_org_sub

class NginxSSIMiddleware(object):
    '''
    Emulates Nginx SSI module for when a page is rendered from Python. SSI include tags are 
    cached for serving directly from Nginx, but if the page is being built for the first time, 
    we just serve these directly from Python without having to make another request.
    
    Takes a response object and returns the response with Nginx SSI tags resolved.
    '''
    def process_response(self, request, response):
        include_tag = r'<!--#[\s.]+include[\s.]+virtual=["\'](?P<path>.+)["\'][\s.]+-->'
        resolver = get_resolver(get_urlconf())
        patterns = resolver._get_url_patterns()
        def get_tag_response(match):
            for pattern in patterns:
                try:
                    view = pattern.resolve(match.group('path')[1:])
                    if view:
                        return view[0](request, *view[1], **view[2]).content
                except Resolver404:
                    pass
            return match.group('path')[1:]
        response.content = re.sub(include_tag, get_tag_response, response.content)
        response['Content-Length'] = len(response.content)
        return response
        

#SETS THE REMOTE_ADDR VARIABLE IN REQUEST TO X_FORWARDED_FOR VARIABLE SENT BY NGINX
class SetRemoteAddrFromForwardedFor(object):
    '''
    Some redundancy here in vars getting push from nginx (real-ip vs remote addys)
    Needs to be straightened out. REMOTE_ADDR used throughout codebase.
    '''
    def process_request(self, request):
        try:
            x_real_ip = request.META['X-REAL-IP']
            verify_ip = IPAddress(x_real_ip)
            request.META['REMOTE_ADDR'] = x_real_ip
        except:
            try:
                forwarded_for = request.META['X-FORWARDED-FOR']             
                forwarded_ip = forwarded_for.split(",")[0]            
                verify_ip = IPAddress(forwarded_ip)
                request.META['REMOTE_ADDR'] = forwarded_ip
            except:
                try:
                    forwarded_for = request.META['X-FORWARDED-FOR']             
                    forwarded_ip = forwarded_for.split(",")[1]
                    real_ip = IPAddress(forwarded_ip)       
                    request.META['REMOTE_ADDR'] = forwarded_ip
                except:
                    pass
