from django.contrib import admin
from models import *
from django.conf import settings
from django.template import RequestContext
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.conf.urls.defaults import *
from django.shortcuts import render_to_response


'''
built the following custom inline model using this page as reference: http://opensource.washingtontimes.com/blog/post/coordt/2009/01/generic-collections-django/
'''

class GenericCollectionInlineModelAdmin(admin.options.InlineModelAdmin):
    ct_field = "content_type"
    ct_fk_field = "object_id"

    def __init__(self, parent_model, admin_site):
        super(GenericCollectionInlineModelAdmin, self).__init__(parent_model, admin_site)
        ctypes = ContentType.objects.all().order_by('id').values_list('id', 'app_label','model')
        elements = ["%s: '%s/%s'" % (id, app_label, model) for id, app_label, model in ctypes]
        self.content_types = "{%s}" % ",".join(elements)

    def get_formset(self, request, obj=None):
        result = super(GenericCollectionInlineModelAdmin, self).get_formset(request, obj)
        result.content_types = self.content_types
        result.ct_fk_field = self.ct_fk_field
        return result

class GenericCollectionTabularInline(GenericCollectionInlineModelAdmin):
    template = 'admin/edit_inline/tabular.html'

class GenericCollectionStackedInline(GenericCollectionInlineModelAdmin):
    template = 'admin/edit_inline/stacked.html'

class FeaturedObjectInline(admin.StackedInline):
    fieldsets = (
        (None, {
            'fields': (('content_type', 'object_id'), 'image', 'title_color', 'text_color', 'byline_color'),
        }),
        ('Advanced', {
            'classes': ('collapse',),
            'fields': (('title', 'byline'), ('description', 'url'),),
        }),
    )

    model = FeaturedObject
    extra = 0
    
class FeaturedSetAdmin(admin.ModelAdmin):
    inlines = [FeaturedObjectInline]
    
    fieldsets = (
        (None, {
            'fields': (('title', 'current'),),
        }),
    )
    
    class Media:
        js = ('admin/scripts/genericcollection.js',)

        
admin.site.register(FeaturedSet, FeaturedSetAdmin)
admin.site.register(SidebarItem)
