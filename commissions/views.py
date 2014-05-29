import datetime
from operator import attrgetter

from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import *
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page

from accounts.decorators import membership_required
from commissions.models import Cycle, Proposal, RankVote, ApprovalVote
from commissions.forms import ProposalForm, ApprovalVoteForm, RankVoteForm
from utils.imaging import create_thumbnail


def handle_uploaded_file(f):
    destination = open('attached_file', 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()

def index(request):
    cycles = Cycle.objects.current()
    archive = Cycle.objects.past()
    today = datetime.datetime.now()

    breadcrumb = (('Programs', '/programs/'), ('Commissions', None))

    flash_msg = False
    if request.GET.get('deleted'):
        flash_msg = True

    return render_to_response(
        'commissions/index.html', {
            'section_title': 'Rhizome Commissions',
            'include_section_header': True,
            'cycles': cycles,
            'archive': archive,
            'today': today,
            'flash_msg': flash_msg,
            'breadcrumb': breadcrumb,
        },
        RequestContext(request) 
    )
    
def procedures(request, object_id):
    cycle = get_object_or_404(Cycle, pk=object_id)
    today = datetime.datetime.now()
    # does this contain hardcoded url?
    breadcrumb = (('Commissions', reverse('commissions_index')), ('Procedures', None))

    return render_to_response(
        'commissions/procedures.html', {   
            'cycle': cycle,
            'today': today,
            'breadcrumb': breadcrumb,
        },
        RequestContext(request) 
    )

@login_required    
def submit(request, object_id):
    cycle = get_object_or_404(Cycle, pk=object_id)   
    user = request.user
    proposal_form = ProposalForm(initial={'author':request.user})
    today = datetime.datetime.now()
        
    if request.method == 'POST':
        proposal_form = ProposalForm(request.POST, request.FILES or None, initial={'author':request.user})
        
        if proposal_form.is_valid():
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.save()
            
            proposal = proposal_form.save(commit=False)
            proposal.cycle = cycle
            proposal.author = user
            proposal.email = user.email
            proposal.username = user.get_full_name()

            if proposal.cycle.is_tumblr_commission:
                proposal.is_public = False
                proposal.allow_comments = False
            
            proposal.save()
            
            # verification of artist accounts for m2m is handled via the form  
            cleaned_user_list = proposal_form.cleaned_data['other_artists_users']        
            
            if cleaned_user_list:
                for user in cleaned_user_list:  
                    proposal.artists.add(user)                          
                
            proposal.save()
            
            if proposal.image:
                # create_thumbnails uses saved image
                proposal.thumbnail = create_thumbnail(proposal.image)
                
            if request.POST['status'] == 'preview':
                proposal.save()
                return redirect('commissions_proposal_preview', proposal_id=proposal.id)
            
            elif request.POST['status'] == 'save':
                proposal.save()
                return HttpResponseRedirect('%s?save=True' % reverse('commissions_proposal_edit', args=[proposal.id]))

            elif request.POST['status'] == 'publish':
                proposal.submitted = 1
                proposal.save()
                proposal.send_published_proposal_notification_email()
                return HttpResponseRedirect('%s?thanks=True' % reverse('commissions_proposal_detail', args=[proposal.id]))
        else:
            proposal_form = ProposalForm(request.POST,request.FILES or None, initial={'author':request.user})
    
    if today > cycle.submission_start_date and today < cycle.submission_end_date:
        return render_to_response(
            'commissions/submit.html', {
                'proposal_form': proposal_form, 
                'cycle': cycle,
            }, 
            RequestContext(request) 
        )
    else:
        return redirect('commissions_index')
   
@login_required
def proposal_edit(request, proposal_id):
    proposal = get_object_or_404(Proposal, pk=proposal_id)
    user = request.user
    proposal_form = ProposalForm(initial={'author':request.user})
    other_artists_list = None
    today = datetime.datetime.now()
    
    if proposal.get_artists():
        other_artists_list = ', '.join(['%s' % artist.email for artist in proposal.get_artists()])
    
    proposal_form = ProposalForm(request.POST or None, request.FILES or None, \
            instance=proposal.id and Proposal.objects.get(id=proposal.id ), \
            initial={'other_artists_users':other_artists_list })
    
    if request.method == 'POST':
        proposal_form = ProposalForm(request.POST or None, request.FILES or None, \
                instance=proposal.id and Proposal.objects.get(id=proposal.id ), \
                initial={'other_artists_users':str(other_artists_list) })

        if proposal_form.is_valid():
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.save()
            
            proposal = proposal_form.save(commit=False)
            
            if request.POST['status'] == 'delete':
                proposal.delete()
                return HttpResponseRedirect('%s?deleted=True' % reverse('commissions_index'))
            
            proposal.author = user
            proposal.email = user.email
            proposal.username = user.get_full_name()
            
            # verification of artist accounts for m2m is handled via the form  
            cleaned_user_list = proposal_form.cleaned_data['other_artists_users']
                
            if cleaned_user_list:
                for user in cleaned_user_list:  
                    proposal.artists.add(user)
                           
            proposal.save()
 
            if proposal.image:
                # create_thumbnails uses saved image
                proposal.thumbnail = create_thumbnail(proposal.image)
            
            if request.POST['status'] == 'preview':
                proposal.save()
                return redirect('commissions_proposal_preview', proposal_id=proposal.id)
            
            elif request.POST['status'] == 'save':
                proposal.save()
                return HttpResponseRedirect('%s?save=True' % reverse('commissions_proposal_edit', args=[proposal.id]))
            
            elif request.POST['status'] == 'publish':
                proposal.submitted = 1
                proposal.save()
                proposal.send_published_proposal_notification_email()
                return HttpResponseRedirect('%s?thanks=True' % reverse('commissions_proposal_detail', args=[proposal.id]))
        else:
            proposal_form = ProposalForm(request.POST,request.FILES or None, initial={'author':request.user})
            
    if request.user == proposal.author \
        and today > proposal.cycle.submission_start_date \
        and today < proposal.cycle.submission_end_date:
        return render_to_response('commissions/submit.html', {'proposal_form':proposal_form, 'cycle':proposal.cycle}, RequestContext(request))
    else:
        return redirect('commissions_index')

def proposal_detail(request, proposal_id):
    proposal = get_object_or_404(Proposal, id=proposal_id, submitted=True, deleted=0)
    today = datetime.datetime.now()

    can_edit = False    
    if request.user == proposal.author:
        can_edit = True    
        
    if proposal.rhizome_hosted:
        if proposal.is_public or request.user == proposal.author or request.user.is_staff:
            return render_to_response(
                'commissions/proposal_detail.html', {
                    'proposal': proposal,
                    'can_edit': can_edit,
                }, 
                RequestContext(request) 
            )   
        else:
            return redirect('commissions_index')

    elif proposal.is_public or request.user == proposal.author or request.user.is_staff:
        return render_to_response(
            'commissions/proposal_detail_iframe.html', {
                'proposal': proposal,
                'can_edit': can_edit,
            }, 
            RequestContext(request)
        )   
    else:
        return redirect('commissions_index')
            
def proposal_preview(request, proposal_id):
    proposal = get_object_or_404(Proposal, id=proposal_id, deleted = 0)

    can_edit = False 
    if request.user == proposal.author:
        can_edit = True 
    
    if proposal.author == request.user:
        if not proposal.rhizome_hosted:
            return render_to_response(
                'commissions/proposal_detail_iframe.html', {
                    'proposal':proposal,
                    'can_edit':can_edit,
                }, 
                RequestContext(request) 
            )   
        else:
            return render_to_response(
                'commissions/proposal_detail.html', {
                    'proposal': proposal,
                    'can_edit': can_edit,
                },
                RequestContext(request) 
            )   
    else:
        return HttpResponseRedirect(reverse(index))

@login_required
@membership_required
def voting(request, object_id):
    '''
    voting landing page. offers overview of voting procedures and links to specific voting pages.
    '''
    cycle = get_object_or_404(Cycle, pk=object_id)
    today = datetime.datetime.now()
    can_vote = False

    if today > cycle.approval_vote_start and today < cycle.ranking_vote_end:    
        return render_to_response('commissions/voting.html', {
                    'can_vote': can_vote,
                    'cycle': cycle,
                    'today': today,
                }, 
                RequestContext(request)
            ) 
    else:
        return redirect('commissions_index') 

@login_required
@membership_required
def approval_voting_wrapper(request, object_id):
    '''
    stage 1 in commissions voting. 
    allows members to go through proposals and decide if meet criteria.
    '''
    cycle = get_object_or_404(Cycle, pk=object_id)
    today = datetime.datetime.now()
    
    prev_votes = [a.proposal_id for a in ApprovalVote.objects \
                    .filter(user = request.user) \
                    .filter(created__gte = cycle.submission_start_date)]
        
    if today > cycle.approval_vote_start and today < cycle.approval_vote_end:
        current_proposal = None
        approval_status = None
                        
        proposals = Proposal.objects \
            .filter(cycle=cycle) \
            .filter(submitted=True) \
            .filter(is_public=True) \
            .exclude(pk__in=prev_votes) \
            .exclude(deleted=True) \
            .order_by('?')
                        
        awaiting_length = len(proposals)
        paginator = Paginator(proposals, 1)
        
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1

        try:
            awaiting_approval = paginator.page(page)
        except (EmptyPage, InvalidPage):
            awaiting_approval = paginator.page(paginator.num_pages)                
        
        if request.GET.get('proposal'):
            proposal_id = request.GET.get('proposal')
            proposal_id = proposal_id.replace('/', '')
            current_proposal = get_object_or_404(Proposal, id = proposal_id)
        else:        
            for p in awaiting_approval.object_list:
                current_proposal = p
        
        #has user voted for this prop yet?
        try:
            approval_vote_for_prop = ApprovalVote.objects.get(user=request.user, proposal=current_proposal) 
            if approval_vote_for_prop.approved:
                approval_status = 'approved'
            if not approval_vote_for_prop.approved:
                approval_status = 'not approved'
        except:
            approval_status = None
        
        if approval_status == 'approved':
            voting_form = ApprovalVoteForm(initial={
                'user': request.user,
                'proposal': current_proposal,
                'approved': True
            })
        elif approval_status == 'not approved':
            voting_form = ApprovalVoteForm(initial={
                'user': request.user,
                'proposal': current_proposal,
                'approved': False,
            })
        else:
            voting_form = ApprovalVoteForm(initial={'user':request.user, 'proposal':current_proposal})
               
        return render_to_response('commissions/approval_voting_wrapper.html', {
                'voting_form': voting_form,
                'awaiting_approval': awaiting_approval,
                'approval_status': approval_status,
                'current_proposal': current_proposal,
                'awaiting_length': awaiting_length,
            }, 
            RequestContext(request) 
        )   
    else:
        return HttpResponseRedirect(reverse('commissions_voting', args=[cycle.id]))
        
@login_required
@membership_required
def indiv_approval_voting_wrapper(request, proposal_id):
    '''
    lays out approval voting for individual proposal given a proposal id
    during approval voting stage (stage 1)
    '''
    proposal = get_object_or_404(Proposal, pk=proposal_id)
    today = datetime.datetime.now()

    if today < proposal.cycle.approval_vote_start or today > proposal.cycle.approval_vote_end:
        return HttpResponseRedirect(reverse('commissions_voting', args=[proposal.cycle.id]))

    # has user voted for this prop yet?
    try:
        approval_vote_for_prop = ApprovalVote.objects.get(user=request.user, proposal=proposal) 
        if approval_vote_for_prop.approved:
            approval_status = 'approved'
        if not approval_vote_for_prop.approved:
            approval_status = 'not approved'
    except:
        approval_status = None
        
    if approval_status == 'approved':
        voting_form = ApprovalVoteForm(initial={'user':request.user, 'proposal':proposal, 'approved':True})
    elif approval_status == 'not approved':
        voting_form = ApprovalVoteForm(initial={'user':request.user, 'proposal':proposal, 'approved':False})
    else:
        voting_form = ApprovalVoteForm(initial={'user':request.user, 'proposal':proposal})
    
    return render_to_response("commissions/indiv_voting_wrapper.html", {
                'voting_form': voting_form,
                'proposal': proposal,
                'approval_status': approval_status
            }, 
            RequestContext(request)
        )   
        
def voting_proposal_detail(request, proposal_id):
    '''
    view that strips out rhizome template and comments and pulls proposal in via iframe on voting wrapper
    part of approval stage views (stage 1)
    '''
    proposal = get_object_or_404(Proposal, pk=proposal_id)
    
    if proposal.rhizome_hosted:
        if proposal.is_public or request.user == proposal.author or request.user.is_staff:
            return render_to_response('commissions/voting_proposal_detail.html', {'proposal':proposal}, RequestContext(request))
        else:
            return redirect('commissions_index')

    elif proposal.is_public or request.user == proposal.author or request.user.is_staff:
        return render_to_response('commissions/proposal_detail_iframe.html', {'proposal':proposal}, RequestContext(request))
    else:
        return redirect('commissions_index')

@login_required
@membership_required   
@csrf_exempt
def ajax_approve(request, proposal_id):
    '''
    ajax method for approving proposals via the approval wrapper
    part of stage 1
    '''
    proposal = get_object_or_404(Proposal, pk=proposal_id)
        
    if request.POST.get('approved') == 'true':
        approval, created = ApprovalVote.objects.get_or_create(proposal=proposal, user=request.user)
        approval.approved = True
        approval.save()
        return HttpResponse('approved')
    elif request.POST.get('approved') == 'false':
        approval, created = ApprovalVote.objects.get_or_create(proposal=proposal, user=request.user)
        approval.approved = False
        approval.save()  
        return HttpResponse('not approved')
    else:    
        return HttpResponse('')

@login_required
@membership_required
def ranking_vote(request, object_id):        
    '''
    allows users to sort proposals in hierarchical order ala member exhibitions
    stage 2 of voting process
    '''
    today = datetime.datetime.now()
    cycle = get_object_or_404(Cycle, pk=object_id)
    
    if today > cycle.ranking_vote_start and today < cycle.ranking_vote_end:
        ranking_finalists = Proposal.objects \
            .filter(cycle=cycle) \
            .filter(rank_vote_finalist=True) \
            .order_by('?')                            

        rank_votes = RankVote.objects \
            .filter(user=request.user) \
            .filter(proposal__in = ranking_finalists) \
            .filter(created__gte = cycle.submission_start_date) \
            .order_by('rank')

        if rank_votes:
            ranking_finalists = [vote.proposal for vote in sorted(rank_votes, key=attrgetter('rank'))]
            initial = {'rankings': ' '.join([str(vote.proposal.id) for vote in rank_votes])}
            voting_form = RankVoteForm(initial=initial)
        else:
            voting_form = RankVoteForm()
            
        if request.method == 'POST':
            voting_form = RankVoteForm(request.POST)
            
            if voting_form.is_valid():
                proposal_ids = voting_form.cleaned_data['rankings'] 
                
                ranked_props = [Proposal.objects.get(pk=int(s.strip().replace(' ',''))) \
                    for s in proposal_ids.split(' ') if s != '' ]
                  
                for i in range(len(ranked_props)):
                    prop = ranked_props[i]
                    rank = i + 1
                    rank_vote, created = RankVote.objects.get_or_create(proposal=prop, user=request.user)
                    rank_vote.rank = rank
                    rank_vote.save()
                return HttpResponseRedirect('%s?updated=True' % reverse('commissions_ranking_vote', args=[cycle.id]))

        return render_to_response('commissions/ranking_vote.html', {
                'ranking_finalists': ranking_finalists,
                'voting_form': voting_form,
                'cycle': cycle,
                'user_rank_votes_length': len(rank_votes),
            }, 
            RequestContext(request) 
        )
    else:
        return redirect('commissions_index')

### new stuff 

from commissions.models import (
    Grant, GrantProposal
)
from django.contrib import messages
from django.shortcuts import render
import json

@login_required
def submit_grant_proposal(request, grant_slug):
    grant = get_object_or_404(Grant, slug=grant_slug)
    proposal = GrantProposal.objects.filter(grant_id=grant.id, user_id=request.user.id)
    if proposal:
        messages.info(request, 'You have already submitted.')
        return redirect('commissions_index')

    if request.method == 'POST':
        data = {}
        for k, v in request.POST.items():
            if k == 'csrfmiddlewaretoken':
                continue
            if type(v) is list and len(v) == 1:
                v = v[0]            
            data[k] = v
        
        proposal = GrantProposal(grant_id=grant.id, user_id=request.user.id, data=json.dumps(data))
        proposal.save()
        messages.success(request, 'We have recieved your submission. Thanks!')
        return redirect('commissions_index')

    return render(request, grant.template, {'grant': grant})
