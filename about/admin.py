from django.contrib import admin
from models import Press, StaffMember


class PressAdmin(admin.ModelAdmin):
    
    class Meta:
        model = Press

class StaffMemberAdmin(admin.ModelAdmin):
    raw_id_fields = ('user',)
    
    class Meta:
        model = StaffMember
        
admin.site.register(Press,PressAdmin)
admin.site.register(StaffMember,StaffMemberAdmin)
