from django.core.urlresolvers import reverse


PRIMARY_NAV = (
    ('Rhizome', reverse('frontpage')),
    ('Journal', reverse('blog_index')),
    ('Artbase', reverse('featured')),
    ('Community', reverse('community')),
    ('Programs', reverse('programs')),
    ('About Us', reverse('about-about')),
    ('Membership', reverse('support_donate')),
)

SUB_NAV = {
    'Journal': (
        ('Artist Profiles', reverse('artist_profiles')),
        ('First Look: New Art Online', 'http://www.newmuseum.org/exhibitions/online'),
    ),
    'Artbase': (
        ('Browse', reverse('browse')),
        ('Member Exhibitions', reverse('member_exhibitions')),
        ('About', reverse('artbase_about')),
        ('Submit', reverse('submit_artwork')),
    ),
    'Community': (
        ('Announce', reverse('announce_index')), 
        ('Discuss', reverse('discuss-index')), 
        ('Portfolios', reverse('portfolios')),
        ('Profiles', reverse('profiles')),
        ('Jobs Board', reverse('jobs')),
        ('Mailing Lists', reverse('mailinglists')),
    ),
    'Programs': (
        ('Events', reverse('programs_events')), 
        ('Commissions', reverse('commissions_index')), 
        ('First Look', reverse('blog_tag_detail', args=['first-look'])),
        ('Seven on Seven', reverse('sevenonseven_landing')),
        ('Internet Subjects', reverse('blog_tag_detail', args=['internet-subjects'])),
        ('Journal', reverse('blog_index')),
        ('Exhibitions', reverse('programs_exhibitions')),
    ),
    'Membership': (
        ('Donate', reverse('support_donate')),
        ('Membership', reverse('individual')),
        ('Organizations', reverse('organization')),
        ('Supporters', reverse('supporters')),
    ),
    'About Us': (
        ('Advertise', 'http://nectarads.com'),
        ('Policy', reverse('about-policy')),
        ('Press', reverse('about-press')),
        ('Rhizome Labs', 'http://labs.rhizome.org'),
    ),
}
