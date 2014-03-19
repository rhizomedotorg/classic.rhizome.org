from django import template


#FB short for FeedBurner 
FB_BASE = 'http://feeds.feedburner.com/'

FB_URLS = {
    'announce': 'rhizome-announce',
    'artbase': 'rhizome-art',
    'discuss': 'rhizome-discuss',
    'events': 'rhizome-announce-events',
    'frontpage': 'rhizome-fp',
    'jobs': 'rhizome-announce-jobs',
    'opportunities': 'rhizome-announce-opportunities'
}

register = template.Library()

@register.simple_tag
def feedburner_url(name):
	return '%s%s/' % (FB_BASE, FB_URLS[name])
