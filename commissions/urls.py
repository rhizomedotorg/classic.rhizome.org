from django.conf.urls.defaults import *

urlpatterns = patterns('commissions.views',
    url(r'^$', 'index', name='commissions_index'),
    url(r'^procedures/(?P<object_id>\d+)/$', 'procedures', name='commissions_procedures'),
    url(r'^submit/(?P<object_id>\d+)/$', 'submit', name='commissions_submit'),

    url(r'^proposal/(?P<proposal_id>\d+)/$', 'proposal_detail', name='commissions_proposal_detail'), 
    url(r'^proposal/(?P<proposal_id>\d+)/view/$', 'proposal_detail', name='commissions_proposal_detail'), 
    url(r'^proposal/(?P<proposal_id>\d+)/edit/$', 'proposal_edit', name='commissions_proposal_edit'),
    url(r'^proposal/(?P<proposal_id>\d+)/preview/$', 'proposal_preview', name='commissions_proposal_preview'),
    url(r'^proposal/(?P<proposal_id>\d+)/voting_view/$', 'voting_proposal_detail', name='commissions_voting_proposal_detail'),
    url(r'^proposal/(?P<proposal_id>\d+)/approve/', 'ajax_approve', name='commissions_ajax_approve'),

    url(r'^voting/(?P<object_id>\d+)/$', 'voting', name='commissions_voting'),
    url(r'^voting/approval/(?P<object_id>\d+)/$', 'approval_voting_wrapper', name='commissions_approval_voting_wrapper'), 
    url(r'^voting/approval/proposal/(?P<proposal_id>\d+)/$', 'indiv_approval_voting_wrapper', name='commissions_indiv_approval_voting_wrapper'), 
    url(r'^voting/ranking/(?P<object_id>\d+)/$', 'ranking_vote', name='commissions_ranking_vote'), 
)