from django.contrib import admin

from discuss.models import DiscussionThread

from threadedcomments.models import ThreadedComment
from threadedcomments.admin import ThreadedCommentsAdmin


class DiscussionThreadAdmin(admin.ModelAdmin):
    raw_id_fields = ('content_type','last_comment')  
    list_display = ('content_object','id','content_type', 'last_comment', 'created', 'is_public', 'is_removed')
    list_filter = ('is_public', 'is_removed')
    date_hierarchy = ('created')
    actions = ['remove_thread', 'approve_thread']

class MyThreadedCommentsAdmin(ThreadedCommentsAdmin):
	raw_id_fields = ['parent', 'user']

admin.site.register(DiscussionThread, DiscussionThreadAdmin)        

admin.site.unregister(ThreadedComment)
admin.site.register(ThreadedComment, MyThreadedCommentsAdmin)
