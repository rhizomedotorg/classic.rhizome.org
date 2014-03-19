from django.contrib import admin
from exhibitions.models import FrontpageExhibition 


class FrontpageExhibitionAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
        
admin.site.register(FrontpageExhibition, FrontpageExhibitionAdmin)
