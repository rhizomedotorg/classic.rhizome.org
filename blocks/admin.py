from django.contrib import admin
from blocks.models import Block 

class BlockAdmin(admin.ModelAdmin):
    list_display = ['ident', 'category', 'text_truncated']
    list_filter = ['category']
    search_fields = ['ident', 'text']

    def text_truncated(self, obj):
        limit = 100
        if len(obj.text) > limit:
            return obj.text[:limit] + '...'
        return obj.text
    text_truncated.short_description = 'text'

admin.site.register(Block, BlockAdmin)