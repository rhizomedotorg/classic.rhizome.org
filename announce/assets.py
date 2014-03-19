from django_assets import Bundle, register

# =============================================================================
# Announcement forms
# =============================================================================

announcement_forms_css = Bundle(
                              'announce/styles/announce.css',
                              'js/datetimepicker/datepicker.css',
                              filters='cssutils',
                              output='announce/styles/forms_packed.css')
register('announcement_forms_css', announcement_forms_css)

announcement_forms_js = Bundle(
                             'js/datetimepicker/Locale.en-US.DatePicker.js',
                             'js/datetimepicker/Picker.js',
                             'js/datetimepicker/Picker.Attach.js',
                             'js/datetimepicker/Picker.Date.js',
                             'js/loadingOverlay.js',
                             filters='jsmin',
                             output='announce/scripts/forms_packed.js')
register('announcement_forms_js', announcement_forms_js)