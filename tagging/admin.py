from django.contrib import admin
from tagging.models import Tag, TaggedItem
from tagging.forms import TagAdminForm

class TagAdmin(admin.ModelAdmin):
    form = TagAdminForm
    list_display  = ('name', 'type', 'slug', 'id',)
    list_filter   = ('type',)
    search_fields = ['name','slug']
    
admin.site.register(Tag, TagAdmin)

class TaggedItemAdmin(admin.ModelAdmin):
    form = TagAdminForm
    list_display  = ('tag', 'content_type', 'object','approved', 'id',)
    list_filter   = ('approved','content_type')
    raw_id_fields = ('content_type','tag')

admin.site.register(TaggedItem,TaggedItemAdmin)




