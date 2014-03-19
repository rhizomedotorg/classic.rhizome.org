import re

from defensio import Defensio
from django.conf import settings


defensio_call = Defensio(settings.DEFENSIO_API_KEY)

def check_post_for_spam_via_defensio(text_to_check):
    # api call to defensio
    doc = {
        'content': text_to_check, 
        'type': 'comment', 
        'platform': 'custom'
    }

    try:     
        status, result = defensio_call.post_document(doc)

        signature = result['defensio-result']['signature']

        status, put_result = defensio_call.put_document(signature, {'allow': 'false'})
        put_result_body = put_result['defensio-result']

        status, get_result = defensio_call.get_document(signature)

        #print '+++++++++++++++++++++'
        #print get_result["defensio-result"]["spaminess"]
        #print '+++++++++++++++++++++'

        if get_result['defensio-result']['spaminess'] >= settings.DEFENSIO_SPAMINESS_CUTOFF_RATING:
            return True
    except:
        pass

    return False

SPAM_TLDS = ('pl',)

SPAM_TERMS = (
    'forex',
    'creatine|kraetyna',
    'insurance',
    'leather[ -]?handbags',
    'best[ -]?price',
    'skin[ -]?tags',
    'payday[ -]?loans',
    'casino|kasyno',
    'earn[ -]?cash',
    'poker[ -]?on[ -]?line',
    'on[ -]?line[ -]?poker',
    'charm[ -]?bracelet',
    'jewelry[ -]?charm',
    'texas[ -]?hold[ -]?em',
    'holdem',
    'lawyer',
    'slot[ -]?machine',
    'erectile[ -]?dysfunction',
    'personal[ -]?injury',
    'binge[ -]?drinking',
    'electronic[ -]?cigarette',
    'viagra',
    'porno',
    'dermatologist',
    'taxi[ -]?service',
    'web[ -]?solutions',
    'website[ -]?design',
    'search[ -]?engine[ -]?optimization',
    'data[ -]?recovery',
    'ac[ -]?compressor',
    'hairdressing',
    'top[ -]?rated[ -]?service',
    'unbeatable[ -]?price',
    'earn(ing)?[ -]?income',
    '(drilling|mining|engineering)[ -]?equipment',
    'vehicle[ -]?transport',
    'transport[ -]?vehicle',
    'roofing',
    'anabolics',
    'internet[ -]?marketing',
    'fitmania',
    'it[ -]?solutions'
    '(car|boat)[ -]?(loan|finance)',
    'duct[ -]?cleaning',
    'seo[ -]?company',
    'profitable[ -]seo',
    'pest[ -]?control',
    'exterminator',
    'hair[ -]?salon',
    'our[ -]?product',
    'brasil[ -]?wax',
    'ultrabook',
    'apparel[ -]?online',
    'kredyt',
    'best[ -]?restaurants',
    '(single|lonely)[ -]?male',
    'similar[ -]?hobbies',
    'polecam',
    'fitness[ -]?routine',
    'strength[ -]?training',
    'fast[ -]?recharge',
    'divorce[ -]?cases',
    'legal[ -]?issues',
    'youtube[ -]?likes',
    'buy[ -]?likes',
    'landscaping',
    'your[ -]?investments',
    'government[ -]?tenders',
    'personal[ -]?jewelry',
    'boat[ -]?repair',
    'poker[ -]?weblog',
    'extensive[ -]?line',
    '(spa|shower|chef)[ -]?salt',
    'best[ -]?discounts',
    'hairdresser',
)

SPAM_TLDS_PATTERN = re.compile(r'(%s)' % '|'.join(SPAM_TLDS), re.IGNORECASE)
SPAM_TERMS_PATTERN = re.compile(r'(%s)' % '|'.join(SPAM_TERMS), re.IGNORECASE)
