from django.conf import settings

MEDIA_PREFIX = getattr(settings, 'BBCODE_MEDIA_PREFIX',
    '/bbcode/')

SMILEY_MEDIA_PREFIX = getattr(settings,
    'BBCODE_SMILEY_MEDIA_PREFIX', '%ssmilies/' % MEDIA_PREFIX)

SMILEY_MEDIA_URL = '%s%s' % (settings.MEDIA_URL,
        SMILEY_MEDIA_PREFIX)
