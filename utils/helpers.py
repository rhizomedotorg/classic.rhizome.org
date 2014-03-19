import re
import gc  
from decimal import *
    
from django.http import Http404
from django.utils.functional import allow_lazy
from django.utils.html import *
from django.utils.http import urlquote
from django.utils.encoding import force_unicode

def clean_html(html):
    ######
    ## clean html input
    ######
    try:
        from BeautifulSoup import BeautifulSoup as Soup
    except ImportError:
        return html
    soup = Soup(html)
    return unicode(soup)

def strip_bbcode(encoded_object):
    ######
    ## remove bbcode from input string
    ######
    if encoded_object:
        p = re.compile(r'\[[^]]+\]')
        return p.sub('', encoded_object)

def bbcode_to_html(bbcode_string):
    ######
    ## transform sting with bbcode to string with html, uses postmarkup lib
    ## http://code.google.com/p/postmarkup/wiki/Usage
    ######
    import bbcode
    converted_string = bbcode.parse(bbcode_string, auto_discover=True)
    return converted_string[0]


# Configuration addons for rhizome_urlize() function.
RHIZOME_LEADING_PUNCTUATION  = ['(', '<strong>','<em>','<', '&lt;']
RHIZOME_TRAILING_PUNCTUATION = ['.', ',', ')', '</strong>','</em>','>', '\n', '&gt;']
rhziome_punctuation_re = re.compile('^(?P<lead>(?:%s)*)(?P<middle>.*?)(?P<trail>(?:%s)*)$' % \
    ('|'.join([re.escape(x) for x in RHIZOME_LEADING_PUNCTUATION]),
    '|'.join([re.escape(x) for x in RHIZOME_TRAILING_PUNCTUATION])))
    
    
def rhizome_urlize(text, trim_url_limit=None, nofollow=False, autoescape=False):
    """
    ADAPTED FROM django.utils.html
    
    #added .edu support and bbcode formatting
    
    Converts any URLs in text into clickable links.

    Works on http://, https://, www. links and links ending in .org, .net or
    .com. Links can have trailing punctuation (periods, commas, close-parens)
    and leading punctuation (opening parens) and it'll still do the right
    thing.

    If trim_url_limit is not None, the URLs in link text longer than this limit
    will truncated to trim_url_limit-3 characters and appended with an elipsis.

    If nofollow is True, the URLs in link text will get a rel="nofollow"
    attribute.

    If autoescape is True, the link text and URLs will get autoescaped.
    """
    
    trim_url = lambda x, limit=trim_url_limit: limit is not None and (len(x) > limit and ('%s...' % x[:max(0, limit - 3)])) or x
    safe_input = isinstance(text, SafeData)
    words = word_split_re.split(force_unicode(text))
    nofollow_attr = nofollow and ' rel="nofollow"' or ''
    for i, word in enumerate(words):
        match = None
        if '.' in word or '@' in word or ':' in word:
            #changed punctuation re for handling bbcode additions such as <em> and <strong> - nh        
            match = rhziome_punctuation_re.match(word) 
        if match:
            lead, middle, trail = match.groups()
            # Make URL we want to point to.
            url = None
            if middle.startswith('http://') or middle.startswith('https://'):
                url = urlquote(middle, safe='/&=:;#?+*')
            elif middle.startswith('www.') or ('@' not in middle and \
                    middle and middle[0] in string.ascii_letters + string.digits and \
                    (middle.endswith('.org') or middle.endswith('.net') or middle.endswith('.com') \
                    or middle.endswith('.edu'))):
                url = urlquote('http://%s' % middle, safe='/&=:;#?+*')
            elif '@' in middle and not ':' in middle and simple_email_re.match(middle):
                url = 'mailto:%s' % middle
                nofollow_attr = ''
            # Make link.
            if url:
                trimmed = trim_url(middle)
                if autoescape and not safe_input:
                    lead, trail = escape(lead), escape(trail)
                    url, trimmed = escape(url), escape(trimmed)
                middle = '<a href="%s"%s>%s</a>' % (url, nofollow_attr, trimmed)
                words[i] = mark_safe('%s%s%s' % (lead, middle, trail))
            else:
                if safe_input:
                    words[i] = mark_safe(word)
                elif autoescape:
                    words[i] = escape(word)
        elif safe_input:
            words[i] = mark_safe(word)
        elif autoescape:
            words[i] = escape(word)
    return u''.join(words)
rhizome_urlize = allow_lazy(rhizome_urlize, unicode)


def split_by(sequence, length, pad=False):
    ######
    ## efficient list splitting (see announce html select boxes for filtering)
    ######
    iterable = iter(sequence)
    def yield_length():
        for i in xrange(length):
            yield iterable.next()
    while True:
        res = list(yield_length())
        if not res:
            raise StopIteration
        if pad and (len(res) < length):
            for i in range(length - len(res)):
                res.append(None)
        yield res
        
def queryset_iterator(queryset, chunksize=1000):  
    ''''' 
    Iterate over a Django Queryset ordered by the primary key 
 
    This method loads a maximum of chunksize (default: 1000) rows in it's 
    memory at the same time while django normally would load all rows in it's 
    memory. Using the iterator() method only causes it to not preload all the 
    classes. 
 
    Note that the implementation of the iterator does not support ordered query sets. 
    '''  
    pk = 0  
    last_pk = queryset.order_by('-pk')[0].pk  
    queryset = queryset.order_by('pk')  
    while pk < last_pk:  
        for row in queryset.filter(pk__gt=pk)[:chunksize]:  
            pk = row.pk  
            yield row  
        gc.collect()  
        
def make_random_string(length=10, allowed_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'):
    from random import choice
    return ''.join([choice(allowed_chars) for i in range(length)])
    
def remove_duplicates_and_preserve_order(seq, idfun=None):  
    '''
    taken from here: http://www.peterbe.com/plog/uniqifiers-benchmark - nh
    '''
    # order preserving 
    if idfun is None: 
        def idfun(x): return x 
    seen = {} 
    result = [] 
    for item in seq: 
        marker = idfun(item) 
        # in old Python versions: 
        # if seen.has_key(marker) 
        # but in new ones: 
        if marker in seen: continue 
        seen[marker] = 1 
        result.append(item) 
    return result

def browse_helper(request, paginator, per_row=5):
    '''
    helper for handling pagination and creating divided rows of objects for directory-type pages, such as artbase browse and accounts profile list
    '''
    
    page = request.GET.get("page")
    if page:
        try:
            page = int(page)
        except ValueError:
            raise Http404
    else:
        page = 1
    paginator.set_current_page(page)
    objects_per_page = len(paginator.object_list())
    return list(split_by(paginator.object_list(), per_row, pad=True))
    
def truncate_text(content, length, suffix='...'):
    return content[:length].rsplit(' ', 1)[0]+suffix

    
def date_range(start_date, end_date):
    '''
    generator function yielding a range of dates
    '''
    import datetime
    for n in range((end_date - start_date).days):
        yield start_date + datetime.timedelta(n)
        
def month_range(start_date, end_date):
    from datetime import date, datetime
    assert start_date <= end_date
    current = start_date.year * 12 + start_date.month - 1
    end_date = end_date.year * 12 + end_date.month - 1
    while current <= end_date:
        yield date(current // 12, current % 12 + 1, 1)
        current += 1