import os
import sys


import djcelery
djcelery.setup_loader()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

sys.path.append('../scripts/')

gettext = lambda s: s

ADMINS = (
    ('Rhizome', 'admin@rhizome.org'),
)

SERVER_EMAIL = 'django@rhizome.org'
DEFAULT_FROM_EMAIL = 'Rhizome <admin@rhizome.org>'
DISCUSS_FROM_EMAIL = 'discuss@rhizome.org'
ANNOUNCE_FROM_EMAIL = 'announce@rhizome.org'

MEMBERSHIP_GROUP_EMAIL = 'Rhizome <membership@rhizome.org>'
ARTBASE_GROUP_EMAIL = 'artbase@rhizome.org'

SUPPORT_CONTACT = ('Rhizome', 'subscribe@rhizome.org')

MANAGERS = ADMINS
SEND_BROKEN_LINK_EMAILS = False

WSGI_APPLICATION = 'rhizome.wsgi.application'

USE_TZ = False 

CELERY_RESULT_BACKEND = 'djcelery.backends.cache.CacheBackend'

ALLOWED_HOSTS = [
    '.rhizome.org', # Allow domain and subdomains
    '.rhizome.com.', # Also allow FQDN and subdomains
]

COMMENT_MAX_LENGTH = 15000

FILE_UPLOAD_MAX_MEMORY_SIZE = 5000000

TIME_ZONE = 'America/New_York'

LANGUAGE_CODE = 'en-us'

USE_I18N = False

MEDIA_ROOT = os.path.join(BASE_DIR, '../site_media/media')
STATIC_ROOT = os.path.join(BASE_DIR, '../site_media/static')

MEDIA_URL = '/media/'
STATIC_URL = '/static/'

SSL_MEDIA_URL = MEDIA_URL 
SSL_STATIC_URL = STATIC_URL

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, '../static'),
)

FILE_UPLOAD_PERMISSIONS = 0644

LANGUAGES = (
    ('en', gettext('English')),
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader', 
    'django.template.loaders.app_directories.Loader',
)

AUTHENTICATION_BACKENDS = (
    'accounts.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    
    #nginx-ssi esi emulation
    'proxy_server.nginxmiddleware.SetRemoteAddrFromForwardedFor',

    'accounts.middleware.OnlineNowMiddleware',
)

ROOT_URLCONF = 'rhizome.urls'

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, '../templates'),
)

# to use ssi template tag
ALLOWED_INCLUDE_ROOTS = TEMPLATE_DIRS

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.debug',
    'rhizome.context_processors.current_campaign',
    'proxy_server.context_processors.ssl_media',
)

AUTH_PROFILE_MODULE = 'accounts.RhizomeUser'
LOGIN_REDIRECT_URL = '/'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.comments',
    'django.contrib.markup',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'tagging',
    
    'inlines',
    'mptt',
    'publisher',
    
    'bbcode',
    'hitcount',
    'easy_thumbnails',
    'threadedcomments',
    'oembed',
    'countries',
    'simplejson',
    'haystack',
    'django_extensions',
    'news_sitemaps',
    'paintstore',
    'tastypie',
    'djcelery',
    'cl2csv',
    'eazyemail',
    'advancedmod',

    # rhizome apps
    'rhizome',
    'blocks',
    'accounts',
    'artbase',
    'blog',
    'discuss',
    'announce',
    'commissions',
    'orgsubs',
    'mailinglists',
    'programs',
    'frontpage',
    'support',
    'about',
    'proxy_server',
    'utils',
    'feeds',
    'sevenonseven',
    'deploy_button',
    'exhibitions',
)

BROKER_URL = 'amqp://'

# django-eazy-email
EAZY_EMAIL_CONTEXT_PROCESSORS = (
    'eazyemail.context_processors.static',
    #'django_eazy_email.context_processors.media',
)

COMMENTS_APP = 'threadedcomments'
COMMENTS_ALLOW_PROFANITIES = True

BLOG_PAGESIZE = 15

HITCOUNT_HITS_PER_IP_LIMIT = 0

# news sitemaps setting
PUBLICATION_NAME = 'Rhizome'

# min user rating/points bypass moderation
MODERATION_CUTOFF_RATING = 5

DEFENSIO_SPAMINESS_CUTOFF_RATING = .60

MIN_DONATION_TO_BECOME_MEMBER = '30.00'
MIN_DONATION_TO_BECOME_COUNCIL = '1000.00'
HIGH_LEVEL_DONATION_CUTOFF = '50.00'
BENEFIT_DONATION_CUTOFF = '300.00'

DEBUG = True 
TEMPLATE_DEBUG = True 
ASSETS_DEBUG = True 

HAYSTACK_SEARCH_RESULTS_PER_PAGE = 25

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

THUMBNAIL_QUALITY = 95

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

INTERNAL_IPS = ('127.0.0.1',)

SITE_ID = 2

try: 
    from local_settings import *
except ImportError:
    pass
