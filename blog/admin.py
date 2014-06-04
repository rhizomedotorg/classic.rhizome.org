from django import forms
from django.contrib import admin
from django.shortcuts import render_to_response
from django.template import RequestContext

from blog.models import (
    Post, ReblogPost, PostMeta, PostImage, PostVideo, PostAudio, PostFile
) 

import zipfile
from django.conf import settings
from django.contrib.sites.models import Site


class PostForm(forms.ModelForm):
    class Meta:
        model = Post 
        widgets = { 
           'body' : forms.Textarea(attrs={'class':'mce-editor'}),
           'fp_news_excerpt' : forms.Textarea(attrs={'class':'mce-editor'}),
           'tags' : forms.TextInput(attrs={'size':'60'}),
           'title' : forms.TextInput(attrs={'size':'60'}),
           'subtitle' : forms.TextInput(attrs={'size':'60'}),
           'slug' : forms.TextInput(attrs={'size':'60'})
        }

    zip_file = forms.Field(widget=forms.FileInput(), required=False)

    def save(self, commit):
        instance = super(PostForm, self).save(commit=False)

        # handle upload
        zfile = self.cleaned_data.get('zip_file')
        if zfile:
            dirname = zfile.name.split('.')[0]
            with zipfile.ZipFile(zfile, 'r') as z:
                z.extractall('%s/%s/' % (settings.MEDIA_ROOT, dirname))
            instance.iframe_src = 'http://%s%s/index.html' % (settings.MEDIA_URL, dirname)

        if commit:
            instance.save()
        return instance

class PostAdmin(admin.ModelAdmin):
    model = Post
    form = PostForm
    list_display  = ('title', 'byline', 'publish', 'status', 'is_micro', 'featured_article')
    list_filter   = ('publish', 'status', 'featured_article', 'is_micro')
    search_fields = ('title', 'body', 'byline', 'authors__username', 'authors__first_name', 'authors__last_name')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'publish'
    raw_id_fields = ('authors',)
    readonly_fields = ('iframe_src',)
    save_on_top = True
    fieldsets = (
        (None, {
            'fields': ('iframe_src', 'zip_file'),
        }),
        (None, {
            'fields': (('title', 'byline'), ('subtitle', 'status'), 'body', ('authors', 'publish'), 'slug', 'tags')
        }),
        ('Options', {
            'fields': ('allow_comments', 'is_live'),
        }),
        ('Categories', {
            'fields': (('featured_article', 'is_micro', 'artist_profile', 'sponsored', 'artbase_essay'),)
        }),
        ('Front Page', {
            'classes' : ('collapse',),
            'fields': ('tease', 'fp_news_excerpt',)
        }),
    )

    class Media:
        js = (
            'js/tinymce/jscripts/tiny_mce/tiny_mce.js',
            'js/tinymce.conf.js',
        )
    
    def get_urls(self):
        from django.conf.urls.defaults import patterns
        return patterns('',
            (r'^byline_to_user/$', self.admin_site.admin_view(self.byline_to_user)), 
        ) + super(PostAdmin, self).get_urls()
    
    def byline_to_user(self, request):
        #takes one user and merges them into another by changing all their content objects' user ids to the new user's id.
        context_instance = RequestContext(request)
        opts = self.model._meta
        admin_site = self.admin_site
        merged_notice = None
        merged_objects = []
        
        preview_objects = None
        preview_notice = None
        
        if request.method == "POST":
        
            if request.POST.get('merge'):
                byline = request.POST.get('merge_byline')
                blog_posts = Post.objects.filter(byline__icontains = byline)

                merge_user = User.objects.get(id = request.POST.get('user'))
                                        
                if blog_posts:
                    for post in blog_posts:
                        post.authors.add(merge_user)
                        merged_objects.append(post)
                                        
                if merged_objects:
                    merged_notice = '%s posts merged' %  len(merged_objects)
                else:
                    merged_notice = '0 posts merged'
                    
            if request.POST.get('view_byline_objects'):
                byline = request.POST.get('preview_byline')
                preview_objects = Post.objects.filter(byline__icontains = byline)
                    
                if preview_objects:
                    preview_notice = 'posts for this byline:'
                else:
                    preview_notice = 'no posts for this byline'
                    
        d = {
            'admin_site': admin_site.name, 
            'title': 'Byline to User', 
            'opts': 'Blog', 
            'app_label': opts.app_label,
            'merged_objects': merged_objects,
            'merged_notice': merged_notice,
            'preview_objects': preview_objects,
            'preview_notice': preview_notice
        }
            
        return render_to_response('admin/blog/byline_to_user.html', d, context_instance)

class PostImageForm(forms.ModelForm):
    class Meta:
        model = PostImage
        widgets = { 
           'title' : forms.TextInput(attrs={'size':'70'})
        }

class PostImageAdmin(admin.ModelAdmin):
    raw_id_fields = ('post',)
    readonly_fields = ('uploaded',)
    list_display = ('admin_thumbnail', 'title', 'post', 'uploaded',)
    list_display_links = ('admin_thumbnail', 'title')
    list_filter = ('uploaded',)
    search_fields = ('title', 'taken_by', 'description', 'post__title')
    form = PostImageForm
    fieldsets = (
        (None, {
            'fields': ('title', 'taken_by', 'image', 'description', 'post')
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if obj:
            return self.fieldsets + (
                ('Important Dates', {
                    'fields': ('uploaded',)
                }),
            )
        return self.fieldsets

class PostVideoForm(forms.ModelForm):
    class Meta:
        model = PostVideo
        widgets = { 
           'title' : forms.TextInput(attrs={'size':'70'})
        }

class PostVideoAdmin(admin.ModelAdmin):
    raw_id_fields = ('post',)
    readonly_fields = ('uploaded',)
    list_display = ('title', 'post', 'uploaded',)
    list_filter = ('uploaded',)
    search_fields = ('title', 'created_by', 'description', 'post__title')

    form = PostVideoForm
    fieldsets = (
        (None, {
            'fields': ('title', 'created_by', 'video', 'description', 'still', 'post')
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if obj:
            return self.fieldsets + (
                ('Important Dates', {
                    'fields': ('uploaded',)
                }),
            )
        return self.fieldsets

class PostAudioForm(forms.ModelForm):
    class Meta:
        model = PostAudio
        widgets = { 
           'title' : forms.TextInput(attrs={'size':'70'})
        }

class PostAudioAdmin(admin.ModelAdmin):
    raw_id_fields = ('post',)
    readonly_fields = ('uploaded',)
    list_display = ('title', 'post', 'uploaded',)
    list_filter = ('uploaded',)
    search_fields = ('title', 'created_by', 'description', 'post__title')
    form = PostAudioForm
    fieldsets = (
        (None, {
            'fields': ('title', 'created_by', 'audio', 'description', 'still', 'post')
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if obj:
            return self.fieldsets + (
                ('Important Dates', {
                    'fields': ('uploaded',)
                }),
            )
        return self.fieldsets

class PostFileForm(forms.ModelForm):
    class Meta:
        model = PostFile
        widgets = { 
           'title' : forms.TextInput(attrs={'size':'70'})
        }

class PostFileAdmin(admin.ModelAdmin):
    raw_id_fields = ('post',)
    readonly_fields = ('uploaded',)
    list_display = ('title', 'post', 'uploaded',)
    list_display_links = ('title',)
    list_filter = ('uploaded',)
    search_fields = ('title', 'created_by', 'description', 'post__title')
    form = PostFileForm
    fieldsets = (
        (None, {
            'fields': ('title', 'created_by', 'file', 'description', 'post')
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if obj:
            return self.fieldsets + (
                ('Important Dates', {
                    'fields': ('uploaded',)
                }),
            )
        return self.fieldsets

admin.site.register(Post, PostAdmin)
admin.site.register(PostFile, PostFileAdmin) 
admin.site.register(PostAudio, PostAudioAdmin)
admin.site.register(PostVideo, PostVideoAdmin)
admin.site.register(PostImage, PostImageAdmin)
#admin.site.register(ReblogPost, ReblogPostAdmin)
