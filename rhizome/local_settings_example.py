DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.sqlite',
    }
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'engine': 'haystack.backends.simple_backend.SimpleEngine',
    },
}

SECRET_KEY = ''
ADMIN_HASH_SECRET = ''

COUCH_SERVER = 'http://127.0.0.1:5984'
DEFENSIO_API_KEY = '' 

PAYPAL_POSTBACK_URL = 'https://www.sandbox.paypal.com/cgi-bin/webscr'
PAYPAL_IDENTITY_TOKEN = ''
PAYPAL_RECEIVER_EMAIL = ''

# authorize.net
AUTHNET_DEBUG = True 
AUTHNET_LOGIN_ID = ''
AUTHNET_TRANSACTION_KEY = ''
AUTHNET_URL = 'https://test.authorize.net/gateway/transact.dll'
