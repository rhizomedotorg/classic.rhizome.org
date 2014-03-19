from django_assets import Bundle, register

# =============================================================================
# Featured
# =============================================================================

artbase_featured_css = Bundle('artbase/styles/artbase.css',
                              'artbase/styles/featured.css',
                              'artbase/styles/collections.css',
                              filters='cssutils',
                              output='artbase/styles/featured_packed.css')
register('artbase_featured_css_all', artbase_featured_css)

artbase_featured_js = Bundle('artbase/scripts/featured-rotate.js',
                             'artbase/scripts/highlights.js',
                             filters='jsmin',
                             output='artbase/scripts/featured_packed.js')
register('artbase_featured_js_all', artbase_featured_js)

# =============================================================================
# Tags
# =============================================================================

artbase_tags_css = Bundle('artbase/styles/tags.css',
                      output='artbase/styles/tags_packed.css')
register('artbase_tags_css_all', artbase_tags_css)

# =============================================================================
# Forms
# =============================================================================

artwork_forms_css = Bundle('artbase/styles/artwork_forms.css',
                           'admin/css/widgets.css',
                            filters='cssutils',
                            output='artbase/styles/artwork_forms_packed.css')
register('artwork_forms_css_all', artwork_forms_css)

artwork_forms_js = Bundle('admin/js/core.js',
                          'admin/js/calendar.js',
                          'admin/js/admin/DateTimeShortcuts.js',
                          'artbase/scripts/tech_lists.js',
                          'artbase/scripts/cc_license.js',
                           filters='jsmin',
                          output='artbase/scripts/artwork_forms_packed.js')
register('artwork_forms_js_all', artwork_forms_js)

# =============================================================================
# Exhibitions
# =============================================================================

exhibitions_css = Bundle('artbase/styles/artbase.css',
                         'artbase/styles/exhibitions.css',
                         'artbase/styles/edit_exhibition.css',
                         filters='cssutils',
                         output='artbase/styles/exhibitions_packed.css')
register('exhibitions_css_all', exhibitions_css)

exhibitions_js = Bundle('artbase/scripts/view_exhibition.js',
                        'artbase/scripts/exhibition.js',
                         filters='jsmin',
                        output='artbase/scripts/exhibition_packed.js')
register('exhibitions_js_all', exhibitions_js)

# =============================================================================
# Browse
# =============================================================================

browse_css = Bundle('artbase/styles/artbase.css',
                    'css/browse.css',
                    filters='cssutils',
                    output='artbase/styles/browse_packed.css')
register('browse_css_all', browse_css)
