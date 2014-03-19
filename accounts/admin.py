import csv
import datetime

from django.conf import settings  
from django.contrib import admin, messages
from django.contrib.auth.forms import AdminPasswordChangeForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.html import escape
from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from accounts.models import *
from accounts.forms import RhizomeUserChangeForm

from cl2csv.options import ExportModelAdmin

# the same filter that I called in the template
# from search.helpers.tags import logic

csrf_protect_m = method_decorator(csrf_protect)

class RhizomeMembershipInline(admin.TabularInline):
        model = RhizomeMembership
        fk_name = "user"
        max_num = 1 
        raw_id_fields = ('org_sub',)
        extra = 0

class UserRatingInline(admin.TabularInline):
        model = UserRating
        fk_name = "user"
        max_num = 1 
        
class ActivityStreamInline(admin.TabularInline):
        model = ActivityStream
        fk_name = "user"

class RhizomeMembershipAdmin(admin.ModelAdmin):
    list_filter = ('complimentary', 'member_tools','archival_access','org_sub_admin',)
    list_display  = ['user','member_tools_exp_date','org_sub','id']
    search_fields = ['^user__email','^user__username','^user__first_name','^user__last_name', '^user__id','org_sub__name']
    save_on_top= True
    raw_id_fields = ('user','org_sub',)
    
admin.site.register(RhizomeMembership, RhizomeMembershipAdmin)

class LocationListFilter(admin.SimpleListFilter):
    title = _('Location')
    parameter_name = 'location'

    def lookups(self, request, model_admin):
        return (
            ('nyc', 'NYC'),
            ('london', 'London'),
            ('la', 'LA'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'nyc':
            return queryset.filter(
                Q(user__useraddress__city__icontains='new york' ) | 
                Q(user__useraddress__city__icontains='brooklyn') |
                Q(user__useraddress__city__iexact='nyc') |
                Q(user__useraddress__city__iexact='ny') |
                Q(user__useraddress__city__iexact='queens')
            ).distinct()

        if self.value() == 'london':
            return queryset.filter(user__useraddress__city__icontains='london').distinct()

        if self.value() == 'la':
            return queryset.filter(
                Q(user__useraddress__city__icontains='los angeles' ) | 
                Q(user__useraddress__city__iexact='la')
            ).distinct()

class MemberListFilter(admin.SimpleListFilter):
    title = _('Member')
    parameter_name = 'member'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(user__user_membership__member_tools=True)

        if self.value() == 'no':
            return queryset.exclude(user__user_membership__member_tools=True)

class RhizomeUserAdmin(ExportModelAdmin):
    list_display  = ('username', 'first_name', 'last_name', 'email', 'is_active', 'is_member', 'date_joined', 'modified')
    list_filter = ('is_staff', 'is_superuser', 'is_active', MemberListFilter, LocationListFilter, 'gender')
    search_fields = ['email', 'username', 'first_name', 'last_name', 'id']
    raw_id_fields = ('user', 'saved_artworks')
    actions = ['make_inactive']
    exclude = ['user',]
    date_hierarchy = ('date_joined')

    form = RhizomeUserChangeForm

    add_form = UserCreationForm
    add_form_template = 'admin/auth/user/add_form.html'
    
    change_password_form = AdminPasswordChangeForm
    change_user_password_template = None
    
    save_on_top= True
    inlines = [RhizomeMembershipInline, UserRatingInline]

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2')}
        ),
    )

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Mark user as inactive"

    '''
    Alot of the below code came from the django user admin code,
    which is not the best way to go about it. I did it early on when Django's
    methods for extending the auth user model were not well documented... nh
    '''
   
    def __call__(self, request, url):
        # this should not be here, but must be due to the way __call__ routes
        # in ModelAdmin.
        if url is None:
            return self.changelist_view(request)
        if url.endswith('password'):
            return self.user_change_password(request, url.split('/')[0])
        return super(RhizomeUserAdmin, self).__call__(request, url)

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super(RhizomeUserAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults.update({
                'form': self.add_form,
                'fields': admin.util.flatten_fieldsets(self.add_fieldsets),
            })
        defaults.update(kwargs)
        return super(RhizomeUserAdmin, self).get_form(request, obj, **defaults)

    def get_urls(self):
        from django.conf.urls.defaults import patterns
        return patterns('',
            (r'^(\d+)/password/$', self.admin_site.admin_view(self.user_change_password)),
            (r'^merge_users/$', self.admin_site.admin_view(self.merge_users)), 
            (r'^membership_overview/$', self.admin_site.admin_view(self.membership_overview)), 
            # (r'^dump_new_members/$', self.admin_site.admin_view(self.dump_new_members)), 
            # (r'^dump_new_users/$', self.admin_site.admin_view(self.dump_new_users)), 
            # (r'^dump_nyc_members/$', self.admin_site.admin_view(self.dump_nyc_members)), 
        ) + super(RhizomeUserAdmin, self).get_urls()

    #add new user view
    @csrf_protect_m
    @transaction.commit_on_success
    def add_view(self, request, form_url='', extra_context=None):
        # It's an error for a user to have add permission but NOT change
        # permission for users. If we allowed such users to add users, they
        # could create superusers, which would mean they would essentially have
        # the permission to change users. To avoid the problem entirely, we
        # disallow users from adding users if they don't have change
        # permission.
        if not self.has_change_permission(request):
            if self.has_add_permission(request) and settings.DEBUG:
                # Raise Http404 in debug mode so that the user gets a helpful
                # error message.
                raise Http404('Your user does not have the "Change user" permission. In order to add users, Django requires that your user account have both the "Add user" and "Change user" permissions set.')
            raise PermissionDenied
        if extra_context is None:
            extra_context = {}
        defaults = {
            'auto_populated_fields': (),
            'username_help_text': self.model._meta.get_field('username').help_text,
        }
        extra_context.update(defaults)
        return super(RhizomeUserAdmin, self).add_view(request, form_url, extra_context)
    
    #change password view
    def user_change_password(self, request, id):
        if not self.has_change_permission(request):
            raise PermissionDenied
        user = get_object_or_404(self.model, pk=id)
        if request.method == 'POST':
            form = self.change_password_form(user, request.POST)
            if form.is_valid():
                new_user = form.save()
                msg = ugettext('Password changed successfully.')
                messages.success(request, msg)
                return HttpResponseRedirect('..')
        else:
            form = self.change_password_form(user)

        fieldsets = [(None, {'fields': form.base_fields.keys()})]
        adminForm = admin.helpers.AdminForm(form, fieldsets, {})

        return render_to_response(self.change_user_password_template or 'admin/auth/user/change_password.html', {
            'title': _('Change password: %s') % escape(user.username),
            'adminForm': adminForm,
            'form': form,
            'is_popup': '_popup' in request.REQUEST,
            'add': True,
            'change': False,
            'has_delete_permission': False,
            'has_change_permission': True,
            'has_absolute_url': False,
            'opts': self.model._meta,
            'original': user,
            'save_as': False,
            'show_save': True,
        }, context_instance=RequestContext(request))
        
    #merge member view
    
    def merge_users(self, request):
        # takes one user and merges them into another by 
        # changing all their content objects' user ids to the new user's id.
        context_instance = RequestContext(request)
        opts = self.model._meta
        admin_site = self.admin_site
        merged_notice = None
        merged_objects = []
        preview_objects = None
        preview_notice = None
        
        if request.method == "POST":
        
            if request.POST.get('merge'):
                old_user = User.objects.get(id = request.POST.get('old_user'))
                merge_user = User.objects.get(id = request.POST.get('merge_user'))
                
                meta_objects = [rel.get_accessor_name() for rel in User._meta.get_all_related_objects()]
                            
                for meta in meta_objects:
                    try:
                        objects = getattr(old_user, meta).all()
                        if objects:
                            for object in objects:
                                # for some reason, printing the object here prevents 
                                # Doesnotexist errors when i try to print the final list. need to fix.
                                print object 
                                object.user = merge_user
                                object.save()
                                merged_objects.append(object)
                    except:
                        pass
                
                blog_posts = old_user.get_profile().get_blog_posts()
                if blog_posts:
                    for post in blog_posts:
                        post.authors.add(merge_user)
                        post.authors.remove(old_user)
                        merged_objects.append(post)
                        
                old_user.is_active = 0
                old_user.save()
                
                if merged_objects:
                    merged_notice = "%s objects merged" %  len(merged_objects)
                else:
                    merged_notice = "0 objects merged"
                    
            if request.POST.get('view_user_objects'):
                preview_user = User.objects.get(id = request.POST.get('preview_user'))
                preview_objects = []
                
                if preview_user:
                    meta_objects = [rel.get_accessor_name() for rel in User._meta.get_all_related_objects()]
                                
                    for meta in meta_objects:
                        try:
                            objects = getattr(preview_user, meta).all()
                            if objects:
                                for object in objects:
                                    # for some reason, printing the object here prevents 
                                    # Doesnotexist errors when i try to print the final list. need to fix.
                                    print object 
                                    preview_objects.append(object)
    
                        except:
                            pass
                                                                       
                    blog_posts = preview_user.get_profile().get_blog_posts()
                    if blog_posts:
                        for post in blog_posts:
                            preview_objects.append(post)            
                    
                if preview_objects:
                    preview_notice = "USER'S OBJECTS:"
                else:
                    preview_notice = "USER HAS NOT OBJECTS"
                    
        d = {'admin_site': admin_site.name, 
             'title': "Merge Users", 
             'opts': "Profiles", 
             'app_label': opts.app_label,
             'merged_objects':merged_objects,
             'merged_notice':merged_notice,
             "preview_objects":preview_objects,
             "preview_notice":preview_notice

             }
            
        return render_to_response('admin/accounts/rhizomeuser/merge_users.html', d, context_instance)
 
       
    def membership_overview(self, request):
        # an overview page for membership

        context_instance = RequestContext(request)
        opts = self.model._meta
        admin_site = self.admin_site
        today =  datetime.datetime.today()
        
        all_member_count = RhizomeMembership.objects.values('id').filter(member_tools = True).count()
        paying_members = RhizomeMembership.objects.values('id').filter(member_tools = True).filter(complimentary=False).filter(org_sub=None).count()
        orgsub_member_count = RhizomeMembership.objects.values('id').filter(member_tools = True).exclude(org_sub=None).count()
        complimentary_members = RhizomeMembership.objects.values('id').filter(member_tools = True).filter(complimentary=True).count()
        
        new_users_this_year = User.objects.values('id').filter(date_joined__year = today.year).count()
        
        one_year_ago = today - datetime.timedelta(365)

        one_year_expired = RhizomeMembership.objects.values('id') \
             .filter(member_tools = False) \
             .filter(complimentary = False) \
             .filter(org_sub = None) \
             .filter(member_tools_exp_date__lte = today) \
             .filter(member_tools_exp_date__gte = one_year_ago) \
             .filter(org_sub_admin = False) \
             .count()

        thirty_days_ago = today - datetime.timedelta(30)
        
        recently_expired = RhizomeMembership.objects \
            .filter(member_tools_exp_date__gte = thirty_days_ago) \
            .filter(member_tools_exp_date__lte = today) \
            .filter(member_tools = False) \
            .filter(complimentary = False) \
            .filter(org_sub_admin = False) \
            .filter(org_sub = None) \
            .order_by('-member_tools_exp_date')

        d = {'admin_site': admin_site.name, 
             'title': "Membership Overview", 
             'opts': "Profiles", 
             'app_label': opts.app_label,
             'all_member_count':all_member_count,
             'paying_members':paying_members,
             'orgsub_member_count':orgsub_member_count,
             'recently_expired':recently_expired,
             'complimentary_members':complimentary_members,
             'one_year_expired':one_year_expired,
             'new_users_this_year':new_users_this_year
             }
        return render_to_response('admin/accounts/rhizomeuser/membership_overview.html', d, context_instance)

    # def dump_new_members(self, request):
    #     '''
    #     creates a csv file dump of new members for importing to mailchimp
    #     '''
        
    #     context_instance = RequestContext(request)
    #     opts = self.model._meta
    #     admin_site = self.admin_site
                    
    #     if request.method == "POST":
        
    #         response = HttpResponse(mimetype='text/csv')

    #         if request.POST.get("one_year"):
    #             backdate = datetime.datetime.now() - timedelta(days=365)  
    #             response['Content-Disposition'] = 'attachment; filename=rhizome_new_members_ONE_YEAR_%s.csv' % (datetime.date.today(),)
            
    #         if request.POST.get("six_months"):
    #             backdate = datetime.datetime.now() - timedelta(days=190)  
    #             response['Content-Disposition'] = 'attachment; filename=rhizome_new_members_SIX_MONTHS_%s.csv' % (datetime.date.today(),)
  
    #         if request.POST.get("three_months"):
    #             backdate = datetime.datetime.now() - timedelta(days=100)   
    #             response['Content-Disposition'] = 'attachment; filename=rhizome_new_members_THREE_MONTHS_%s.csv' % (datetime.date.today(),)

    #         if request.POST.get("one_month"):
    #             backdate = datetime.datetime.now() - timedelta(days=32)   
    #             response['Content-Disposition'] = 'attachment; filename=rhizome_new_members_ONE_MONTH_%s.csv' % (datetime.date.today(),)

    #         if request.POST.get("all_time"):
    #             backdate = None
    #             response['Content-Disposition'] = 'attachment; filename=rhizome_ALL_members_%s.csv' % (datetime.date.today(),)


    #         writer = csv.writer(response)            
            
    #         if backdate:
    #             new_members = RhizomeMembership.objects.filter(member_tools = True).filter(last_donation__post_date__gte = backdate)  
    #         else:
    #             new_members = RhizomeMembership.objects.filter(member_tools = True) 

    #         if new_members:
    #             for member in new_members:
    #                 try:
    #                     # try b/c some legacy users may not exist or
    #                     # mayhave bad data not easily encoded
    #                     user = member.user
    #                     if user.first_name:
    #                         writer.writerow([
    #                             '%s' % user.email, 
    #                             '%s' % user.first_name, 
    #                             '%s' % user.last_name, 
    #                         ])
    #                     else:
    #                         writer.writerow([
    #                             '%s' % user.email, 
    #                             '%s' % user.get_profile(), 
    #                             '%s' % "", 
    #                         ])
    #                 except:
    #                     pass
                        
    #         return response
        
    #     d = {'admin_site': admin_site.name, 
    #          'title': "Dump a CSV file of New Members", 
    #          'opts': "Profiles", 
    #          'app_label': opts.app_label,
    #          }
    #     return render_to_response('admin/accounts/rhizomeuser/dump_new_members.html', d, context_instance)    


    # def dump_nyc_members(self, request):
    #     '''
    #     creates a csv file dump of nyc based members for importing to mailchimp
    #     '''
    
    #     context_instance = RequestContext(request)
    #     opts = self.model._meta
    #     admin_site = self.admin_site
                    
    #     if request.method == "POST":
    #         if request.POST.get("nyc"):
    #             response = HttpResponse(mimetype='text/csv')
    #             response['Content-Disposition'] = 'attachment; filename=rhizome_nyc_members%s.csv' % (datetime.date.today(),)
    #             writer = csv.writer(response)            
    #             nyc_addys = UserAddress.objects.filter(Q(city__icontains="New York" ) | Q(city__icontains="NYC" ))
    #             nyc_members = []
                
    #             for a in  nyc_addys:
    #                 try:
    #                     if a.user.get_profile().is_member():
    #                         nyc_members.append(a.user)
    #                 except ObjectDoesNotExist:
    #                     pass
                        
    #             nyc_members = list(set(nyc_members))
                
    #             if nyc_members:
    #                 for user in nyc_members:                    
    #                     if user.first_name:
    #                         writer.writerow([
    #                             '%s' % user.email, 
    #                             '%s' % user.first_name, 
    #                             '%s' % user.last_name, 
    #                         ])
    #                     else:
    #                         writer.writerow([
    #                             '%s' % user.email, 
    #                             '%s' % user.get_profile(), 
    #                             '%s' % "", 
    #                         ])
                            
    #             return response
        
    #     d = {'admin_site': admin_site.name, 
    #          'title': "Dump a CSV file of NYC Members", 
    #          'opts': "Profiles", 
    #          'app_label': opts.app_label,
    #          }
    #     return render_to_response('admin/accounts/rhizomeuser/dump_nyc_members.html', d, context_instance)    

    # def dump_new_users(self, request):
    #     '''
    #     creates a csv file dump of new users for importing to mailchimp
    #     '''
    #     context_instance = RequestContext(request)
    #     opts = self.model._meta
    #     admin_site = self.admin_site
                    
    #     if request.method == "POST":
        
    #         response = HttpResponse(mimetype='text/csv')
    #         if request.POST.get("one_year"):
    #             backdate = datetime.datetime.now() - timedelta(days=365)  
    #             response['Content-Disposition'] = 'attachment; filename=rhizome_new_users_ONE_YEAR_%s.csv' % (datetime.date.today(),)
                
    #         if request.POST.get("six_months"):
    #             backdate = datetime.datetime.now() - timedelta(days=190)  
    #             response['Content-Disposition'] = 'attachment; filename=rhizome_new_users_SIX_MONTHS_%s.csv' % (datetime.date.today(),)
  
    #         if request.POST.get("three_months"):
    #             backdate = datetime.datetime.now() - timedelta(days=100)   
    #             response['Content-Disposition'] = 'attachment; filename=rhizome_new_users_THREE_MONTHS_%s.csv' % (datetime.date.today(),)

    #         if request.POST.get("one_month"):
    #             backdate = datetime.datetime.now() - timedelta(days=32)   
    #             response['Content-Disposition'] = 'attachment; filename=rhizome_new_users_ONE-MONTH_%s.csv' % (datetime.date.today(),)

    #         writer = csv.writer(response)            
                                    
    #         new_users = RhizomeUser.objects.filter(date_joined__gte = backdate)  
    #         filtered = [user for user in new_users if not user.is_rhizomemember()]
                        
    #         if filtered:
    #             for user in filtered:                    
                    
    #                 if user.first_name:
    #                     writer.writerow([
    #                         '%s' % user.email, 
    #                         '%s' % user.first_name, 
    #                         '%s' % user.last_name, 
    #                     ])
    #                 else:
    #                     writer.writerow([
    #                         '%s' % user.email, 
    #                         '%s' % user.get_profile(), 
    #                         '%s' % "", 
    #                     ])
                        
    #         return response
        
    #     d = {'admin_site': admin_site.name, 
    #          'title': "Dump a CSV file of New Users", 
    #          'opts': "Profiles", 
    #          'app_label': opts.app_label,
    #          }
    #     return render_to_response('admin/accounts/rhizomeuser/dump_new_users.html', d, context_instance)  

class UserAddressAdmin(admin.ModelAdmin):
    search_fields = ['user__email','user__username','user__first_name','user__last_name','city','state__name', 'country__name',]
    list_display  = ['user','city','street1','street2','state','country','created']
    raw_id_fields = ('user','country','state')

admin.site.register(UserAddress, UserAddressAdmin)
admin.site.register(RhizomeUser, RhizomeUserAdmin)
