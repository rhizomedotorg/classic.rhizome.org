import hashlib
import re

from django import template  
from django.conf import settings

register = template.Library()    
 
@register.filter()  
def hash(type, id):  
    hash = hashlib.md5()  
    hash.update("%s:%s:%s" % (type, id, settings.ADMIN_HASH_SECRET))  
    return hash.hexdigest().upper()  

#http://djangosnippets.org/snippets/312/
r_nofollow = re.compile('<a (?![^>]*nofollow)')
s_nofollow = '<a rel="nofollow" '

@register.filter()
def nofollow(value):
    return r_nofollow.sub(s_nofollow, value)
