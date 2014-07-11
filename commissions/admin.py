from django.contrib import admin

from django.contrib import admin
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect,HttpResponse  
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from utils.helpers import strip_bbcode,split_by
from utils.unicode_csv_writer import UnicodeWriter

from models import *


class CycleAdmin(admin.ModelAdmin):
    raw_id_fields = ('jury_award_winners_proposal','user_vote_winners_proposal','winner_proposal_deprecated','winner_artwork')
    
    class Meta:
        model = Cycle
        
#admin.site.register(Cycle,CycleAdmin)

class ProposalAdmin(admin.ModelAdmin):
    search_fields = ['artists__email','artists__username','artists__last_name','artists__id','author__email','author__username','author__last_name','author__id',
    'summary','title', '^city','state__name','state__abbrev','country__iso','country__printable_name','id']
    raw_id_fields = ('artists','author','state','country')
    list_display  = ['title','author','cycle','id']
    list_filter = ('cycle', 'rhizome_hosted','is_public','submitted', "finalist","rank_vote_finalist")
    
    class Meta:
        model = Proposal
    
    def get_urls(self):
        from django.conf.urls.defaults import patterns
        return patterns('',
            (r'^get_current_proposals/$', self.admin_site.admin_view(self.get_current_proposals)), 
            (r'^filter_proposals/$', self.admin_site.admin_view(self.filter_proposals)), 
            (r'^current_finalists/$', self.admin_site.admin_view(self.current_finalists)), 
            (r'^get_current_finalists/$', self.admin_site.admin_view(self.get_current_finalists)), 
        ) + super(ProposalAdmin, self).get_urls()

    def current_finalists(self, request):
        context_instance = RequestContext(request)
        opts = self.model._meta
        admin_site = self.admin_site 

        finalists = Proposal.objects.current_finalists()
            
        paginator = Paginator(finalists, 1)
        
        # Make sure page request is an int. If not, deliver first page.
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1

        # If page request (9999) is out of range, deliver last page of results.
        try:
            awaiting_approval = paginator.page(page)
        except (EmptyPage, InvalidPage):
            awaiting_approval = paginator.page(paginator.num_pages)
            
        if request.method == "POST":
            finalist = request.POST.get("finalist")
            proposal_id  = request.POST.get("id")   
            proposal = Proposal.objects.get(pk = proposal_id)

            if finalist == "on":
                proposal.finalist = 1
            else:
                proposal.finalist = 0                
            proposal.save()
            
            return HttpResponseRedirect("%s" % request.build_absolute_uri())
        
        d = {
            'admin_site': admin_site.name, 
            'title': "Current Finalists for Judges", 
            'opts': "Proposals", 
            'app_label': opts.app_label,
            'awaiting_approval':awaiting_approval
         }
             
        return render_to_response('admin/commissions/proposals/filter_proposals.html', d, context_instance)    

    def filter_proposals(self, request):
        '''
        allows the staff to filter proposals for judges
        '''
        context_instance = RequestContext(request)
        opts = self.model._meta
        admin_site = self.admin_site 

        current_proposals = Proposal.objects.current()
        current_proposals_count = len(current_proposals)

        divisor = current_proposals_count / 2
        
        split_proposals =  list(split_by(current_proposals, divisor))
                
        paginator = Paginator(current_proposals, 1)
        
        # Make sure page request is an int. If not, deliver first page.
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1

        # If page request (9999) is out of range, deliver last page of results.
        try:
            awaiting_approval = paginator.page(page)
        except (EmptyPage, InvalidPage):
            print request.path
            return HttpResponseRedirect("%s" % request.path)
            
        if request.method == "POST":
            finalist = request.POST.get("finalist")
            proposal_id  = request.POST.get("id")   
            proposal = Proposal.objects.get(pk = proposal_id)

            if finalist == "on":
                proposal.finalist = 1
            else:
                proposal.finalist = 0                
            proposal.save()
            
            return HttpResponseRedirect("%s" % request.build_absolute_uri())
        
        d = {
            'admin_site': admin_site.name, 
            'title': "Filter proposals for Judges", 
            'opts': "Proposals", 
            'app_label': opts.app_label,
            'awaiting_approval':awaiting_approval
        }
             
        return render_to_response('admin/commissions/proposals/filter_proposals.html', d, context_instance)    

    def dump_proposal_csv(self, request, proposals, fname):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s' % fname
        writer = UnicodeWriter(response)
        writer.writerow(['CYCLE', 'TITLE', 'ARTIST', 'URL', 'SUBMITTED','SUMMARY','DESCRIPTION', 'TIMELINE & BUDGET', 'RESUME OR CV', 'WORK SAMPLES', 'CITY', 'STATE', 'COUNTRY']) 
        for proposal in proposals:
            writer.writerow([
                '%s' % proposal.cycle, 
                '%s' % proposal.title, 
                '%s' % proposal.username, 
                '%s' % proposal.view_url(), 
                '%s' % proposal.submitted, 
                '%s' % strip_bbcode(proposal.summary), 
                '%s' % strip_bbcode(proposal.description), 
                '%s' % strip_bbcode(proposal.timeline_and_budget), 
                '%s' % strip_bbcode(proposal.resume_or_cv), 
                '%s' % strip_bbcode(proposal.work_samples), 
                '%s' % proposal.city, 
                '%s' % proposal.state, 
                '%s' % proposal.country, 
            ])
        return response

    def get_current_proposals(self, request):
        context_instance = RequestContext(request)
        opts = self.model._meta
        admin_site = self.admin_site

        if request.method == "POST":
            return self.dump_proposal_csv(request, Proposal.objects.current(), 'submitted_commissions_proposals.csv')

        d = {
            'admin_site': admin_site.name, 
            'title': "Dump a CSV file of the current cycle's submitted proposals", 
            'opts': "Proposals", 
            'app_label': opts.app_label,
        }
             
        return render_to_response('admin/commissions/proposals/latest_proposals.html', d, context_instance)

    def get_current_finalists(self, request):
        context_instance = RequestContext(request)
        opts = self.model._meta
        admin_site = self.admin_site
                
        if request.method == "POST":
            return self.dump_proposal_csv(request, Proposal.objects.current_finalists(), 'commissions_finalists.csv')
                    
        d = {
            'admin_site': admin_site.name, 
            'title': "Dump a CSV file of the finalists", 
            'opts': "Proposals", 
            'app_label': opts.app_label,
        }
             
        return render_to_response('admin/commissions/proposals/dump_finalists.html', d, context_instance)    
                 
#admin.site.register(Proposal,ProposalAdmin)

class RankVoteAdmin(admin.ModelAdmin):
    search_fields = ['user__email','user__username','user__last_name','user__id','user__email',]
    raw_id_fields = ('user','proposal',)
    list_display  = ['proposal','user','rank','created','id']
    date_hierarchy = ('created')

#admin.site.register(RankVote,RankVoteAdmin)

class ApprovalVoteAdmin(admin.ModelAdmin):
    search_fields = ['user__email','user__username','user__last_name','user__id','user__email',]
    raw_id_fields = ('user','proposal',)
    list_display  = ['proposal','user','approved','created','id']
    date_hierarchy = ('created')

#admin.site.register(ApprovalVote,ApprovalVoteAdmin)

### new stuff

import csv

from django.conf.urls import url
from django.http import HttpResponse


class GrantAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('__unicode__', 'voting_enabled', 'number_of_proposals', 'download_proposals')
    raw_id_fields = ('confirmation_email',)

    def get_urls(self):
        urls = super(GrantAdmin, self).get_urls()
        my_urls = [
            url(r'^download-proposals/(?P<grant_slug>[-\w]+)/$', self.proposals_csv),
        ]
        return my_urls + urls

    def download_proposals(self, obj):
        return '<a href="download-proposals/%s">Download</a>' % obj.slug
    download_proposals.allow_tags = True
    download_proposals.short_description = 'proposal spreadsheet'

    def proposals_csv(self, request, grant_slug):
        grant = Grant.objects.get(slug=grant_slug)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s.csv"' % grant.slug

        writer = csv.writer(response)

        headers = grant.proposal_data_headers
        data = grant.proposal_data
        writer.writerow(headers)
        [writer.writerow([d.get(h) for h in headers]) for d in data]

        return response

class GrantProposalAdmin(admin.ModelAdmin):
    raw_id_fields = ('grant',)
    list_display = ('__unicode__', 'created')
    list_filter = ('grant', 'created')

admin.site.register(Grant, GrantAdmin)
admin.site.register(GrantProposal, GrantProposalAdmin)
