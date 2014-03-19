from django.conf import settings

def ssl_media(request):
    try:
        is_https = request.META['HTTP_X_FORWARDED_PROTOCOL']
    except:
        is_https = False
    
    context_media_url = settings.MEDIA_URL
    context_static_url = settings.STATIC_URL  

    if request.is_secure() or is_https:
        context_media_url = settings.SSL_MEDIA_URL
        context_static_url = settings.SSL_STATIC_URL

    return {
        'MEDIA_URL': context_media_url,
        'STATIC_URL': context_static_url,
    }
