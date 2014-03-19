from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string

from moderation.models import QueuedInstance
from moderation.utils import moderator


class QueuedInstanceProxy(QueuedInstance):
    class Meta:
        proxy = True
        verbose_name = "questionable content"
        verbose_name_plural = verbose_name

class ContentTypeListFilter(admin.SimpleListFilter):
    title = 'kind'
    parameter_name = 'content_type'

    def lookups(self, request, model_admin):
        return [(str(ct.id), ct.model_class()._meta.verbose_name.title()) for ct in ContentType.objects.all() 
            if ct.model_class() in [k for k, v in moderator._registry.items()]]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(content_type=self.value())
        return queryset

class ModelModeratorAdmin(admin.ModelAdmin):
    actions = ('mark_spam', 'approve')
    list_display = ['rendered_info']
    list_filter = [ContentTypeListFilter]
    admin_template = 'default.html'

    def __init__(self, *args, **kwargs):
        super(ModelModeratorAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None, )

    def queryset(self, request):
        qs = super(ModelModeratorAdmin, self).queryset(request)
        return qs.filter(awaiting_moderation=True)

    def get_actions(self, request):
        actions = super(ModelModeratorAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def has_add_permission(self, request):
        return False

    def mark_spam(modeladmin, request, queryset):
        for obj in queryset:
            obj.moderate(request, fail=True)
            
    def approve(modeladmin, request, queryset):
        for obj in queryset:
            obj.moderate(request)

    def rendered_info(self, obj):
        return render_to_string(self.admin_template, obj.admin_info())
    rendered_info.allow_tags = True
    rendered_info.short_description = ''

# admin.site.register(QueuedInstance)
admin.site.register(QueuedInstanceProxy, ModelModeratorAdmin)
