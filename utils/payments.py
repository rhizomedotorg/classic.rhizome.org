import urllib2, urllib

from django.conf import settings

############## AUTHORIZE.NET ######################
"""
authorize.net code lifted from http://stackoverflow.com/questions/1637902/python-django-which-authorize-net-library-should-i-use
"""

AUTHORIZE_URL = settings.AUTHNET_URL

if settings.AUTHNET_DEBUG:
    AUTHORIZE_API = {'x_login':settings.AUTHNET_LOGIN_ID, 'x_tran_key':settings.AUTHNET_TRANSACTION_KEY, 'x_method':'CC', 'x_type':'AUTH_CAPTURE', 'x_delim_data':'TRUE', 'x_duplicate_window':'10', 'x_delim_char':'|', 'x_relay_response':'FALSE', 'x_version':'3.0'}

else:
    AUTHORIZE_API = {'x_login':settings.AUTHNET_LOGIN_ID, 'x_password':settings.AUTHNET_TRANSACTION_KEY, 'x_method':'CC', 'x_type':'AUTH_CAPTURE', 'x_delim_data':'TRUE', 'x_duplicate_window':'10', 'x_delim_char':'|', 'x_relay_response':'FALSE', 'x_version':'3.0'}    

def call_authorizedotnet(amount, card_num, exp_date, card_code, address, city, state, zip_code, country, first_name, last_name, user_id, user_email, description):
    '''Call authorize.net and get a result dict back'''
    import urllib2, urllib
    payment_post = AUTHORIZE_API
    payment_post['x_amount'] = amount
    payment_post['x_card_num'] = card_num
    payment_post['x_exp_date'] = exp_date
    payment_post['x_card_code'] = card_code
    if address:
        payment_post['x_address'] = address
    if city:
        payment_post['x_city'] = city
    if state:
        payment_post['x_state'] = state
    if zip_code:
        payment_post['x_zip'] = zip_code
    if country:
        payment_post['x_country'] = country
    payment_post['x_first_name'] = first_name
    payment_post['x_last_name'] = last_name
    payment_post['x_cust_id'] = user_id
    payment_post['x_email'] = user_email
    payment_post['x_description'] = description
    payment_post['x_email_customer'] = False
    payment_post['x_test_request'] = settings.AUTHNET_DEBUG 
    
    payment_request = urllib2.Request(AUTHORIZE_URL, urllib.urlencode(payment_post))
    r = urllib2.urlopen(payment_request).read()
    return r

def call_authorizedotnet_capture(trans_id): # r.split('|')[6] we get back from the first call, trans_id
    capture_post = AUTHORIZE_API
    capture_post['x_type'] = 'PRIOR_AUTH_CAPTURE'
    capture_post['x_trans_id'] = trans_id
    capture_request = urllib2.Request(AUTHORIZE_URL, urllib.urlencode(capture_post))
    r = urllib2.urlopen(capture_request).read()
    return r