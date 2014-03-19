from django import forms
from django.contrib import admin

from programs.forms import RhizEventForm, ExhibitionForm
from programs.models import (
    DownloadFile, DownloadOfTheMonth, Exhibition, RhizEvent, Video
)


class RhizEventAdmin(admin.ModelAdmin):
    list_display  = ['title','start_date','url']
    search_fields = ['^title','^summary','description','url']
    raw_id_fields = ('location_state','location_country','curator')
    date_hierarchy = ('start_date')
    form = RhizEventForm
    add_form = RhizEventForm
    prepopulated_fields = {"slug": ("title",)}

    class Meta:
        model = RhizEvent
    
    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        obj.save()

class ExhibitionAdmin(admin.ModelAdmin):
    list_display  = ['title','start_date','url']
    search_fields = ['^title','^description','url']
    raw_id_fields = ('location_state','location_country','curator','artists')
    date_hierarchy = ('start_date')
    form = ExhibitionForm
    add_form = ExhibitionForm
    prepopulated_fields = {"slug": ("title",)}
    class Meta:
        model = Exhibition
    
    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        obj.save()

class VideoAdmin(admin.ModelAdmin):
    raw_id_fields = ('related_event','related_exhibition','related_post')
    
    class Meta:
        model = Video
    
    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        obj.save()

class DownloadFileInline(admin.TabularInline):
    model = DownloadFile
    extra = 0

class DownloadForm(forms.ModelForm):
    class Meta:
        model = DownloadOfTheMonth 
        widgets = { 
           'file_description_and_size': forms.TextInput(attrs={'size':'100'})
        }

class DownloadOfTheMonthAdmin(admin.ModelAdmin):
    readonly_fields = ('created',)
    inlines = [DownloadFileInline,]
    raw_id_fields = ('artist_user_account',)
    list_display = ('__unicode__', 'premier_date', 'is_active')
    list_filter = ('is_active', 'premier_date')
    search_fields = ('title', 'artist_name')
    form = DownloadForm
    fieldsets = (
        (None, {
            'fields': (
                ('title', 'is_active'),
                ('artist_name', 'artist_user_account'),
                'about_artist', 
                'artist_url', 
                'file_description_and_size', 
                'work_description',
                'work_instructions',
            )
        }),
        ('Important Dates', {
            'fields': ('premier_date', 'created',)
        }),
        ('Images', {
            'fields': ('image', 'artist_image')
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return (
                (None, {
                    'fields': (
                        'title', 
                        ('artist_name', 'artist_user_account'),
                        'about_artist', 
                        'artist_url', 
                        'file_description_and_size', 
                        'work_description',
                        'work_instructions',
                    )
                }),
                ('Important Dates', {
                    'fields': ('premier_date',)
                }),
                ('Options', {
                    'fields': ('is_active',)
                }),
            )
        return self.fieldsets

admin.site.register(RhizEvent, RhizEventAdmin)
admin.site.register(Exhibition, ExhibitionAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(DownloadOfTheMonth, DownloadOfTheMonthAdmin)
