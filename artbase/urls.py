from django.conf.urls.defaults import *
from django.http import HttpResponseRedirect

urlpatterns = patterns(
    'artbase.views',
    url(r'^$', 'featured', name='featured'),
    
    #old forwarding
    url(r'^(?P<id>\d+)/$', 'artwork_forward'), #/artbase/id_number
    url(r'artwork_forward/$', 'artwork_forward'), #/object.rhiz/php?id_number

    # Featured / Landing Page
    #url(r'^featured/$', 'featured', name="featured"), #old featured design
    url(r'^featured/$', 'featured', name="featured"),
    url(r'^fragments/featured_work/(?P<id>\d+)/$', 'featured_fragment'),
    url(r'^fragments/featured_list/(?P<list_type>.+)/$', 'featured_list'),

    # Artworks
    url(r'^artwork/(?P<id>\d+)/$', 'artwork'),
    url(r'^artwork/(?P<id>\d+)/edit/base/$', 'edit_artwork_base', name="edit_artwork_base"),
    url(r'^artwork/(?P<id>\d+)/edit/details/$', 'edit_artwork_details', name="edit_artwork_details"),
    url(r'^artwork/(?P<id>\d+)/edit/media/$', 'edit_artwork_media', name="edit_artwork_media"),
    url(r'^artwork/(?P<id>\d+)/edit/license/$', 'edit_artwork_license', name="edit_artwork_license"),
    url(r'^artwork/(?P<id>\d+)/edit/$', 'edit_artwork_base'),

    url(r'^artwork/(?P<id>\d+)/publish/$', 'publish_artwork'),
    url(r'^artwork/(?P<id>\d+)/delete/$', 'delete_artwork', name="delete_artwork"),
    url(r'^artwork/(?P<id>\d+)/preview/$', 'preview_artwork', name="preview_artwork"),
    url(r'^submit/$', 'submit', name="submit_artwork"),
    url(r'^submitted/$', 'submitted'),

    #Policy
    url(r'^policy/$', 'policy'),

    #About
    url(r'^about/$', 'about', name="artbase_about"),

    #Collections
    url(r'^collections/$', 'collections_index'),
    url(r'^collections/(?P<collection_id>\d+)/$', 'collection_detail'),
    url(r'^collections/artwork/(?P<work_id>\d+)/fragment.html', 'collection_artwork_fragment'),

    # Browse
    url(r'^browse/$', 'browse_by_title', name="browse"),
    url(r'^browse/title/$', 'browse_by_title', name="browse_artbase"),
    url(r'^browse/archived/$', 'browse_by_archived', name="browse_by_archived"),
    url(r'^browse/artist/$', 'browse_by_artist', name="browse_by_artist"),
    url(r'^browse/tag/$', 'browse_by_tag', name="browse_by_tag"),
    url(r'^browse/favorites/$', 'browse_by_favorites', name="browse_by_favorites"),

    # Exhibitions
    url(r'^exhibitions/$', 'member_exhibitions', name='member_exhibitions'),
    url(r'^exhibitions/new/$', 'new_member_exhibition', name="new_member_exhibition"),
    url(r'^exhibitions/edit/$', 'edit_member_exhibition'),
    url(r'^exhibitions/view/(?P<id>\d+)/$', 'view_member_exhibition'),
    url(r'^exhibitions/edit/(?P<id>\d+)/$', 'edit_member_exhibition', name="edit_member_exhibition"),
    url(r'^exhibitions/edit/(?P<id>\d+)/add_work/$', 'edit_member_exhibition_add_work'),
    url(r'^exhibitions/edit/(?P<id>\d+)/remove_work/$', 'edit_member_exhibition_remove_work'),
    url(r'^exhibitions/preview/(?P<id>\d+)/$', 'preview_member_exhibition'),
    url(r'^exhibitions/delete/(?P<id>\d+)/$', 'delete_member_exhibition', name="delete_member_exhibition"),
    url(r'^exhibitions/tag/(?P<slug>[a-z0-9_ -@.]+)/$', 'member_exhibitions_tag'),

    # Tags
    url(r'^tag/$', 'tag'),
    url(r'^tag/(?P<slug>[a-z0-9_ -@.]+)/$', 'tag'),
    
    # AJAX FOR FORMS
    url(r'^get_tech_types/$', 'get_tech_types', name="get_tech_types"),
    url(r'^get_tech_versions/$', 'get_tech_versions', name="get_tech_versions"),
)
