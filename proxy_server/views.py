from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render_to_response
from django.template.context import RequestContext

    
def topnav_login(request):
    return render_to_response(
        'fragments/topnav_login.html', 
        {}, 
        context_instance=RequestContext(request))

def blog_comment_fragment(request):
    post_id = request.GET.get('post_id')
    from blog.models import Post
    post = Post.objects.get(pk = post_id)
    return render_to_response(
            'blog/comment_fragment.html', 
            {'post':post}, 
            context_instance=RequestContext(request))

def announce_comment_fragment(request):
    announcement_id = request.GET.get('announcement_id')
    announcement_ct = request.GET.get('ct')
    content_type = ContentType.objects.get(name = announcement_ct)
    announcement = content_type.get_object_for_this_type(pk = announcement_id)
    return render_to_response(
            'announce/comment_fragment.html', 
            {'announcement':announcement}, 
            context_instance=RequestContext(request))

def commissions_comment_fragment(request):
    proposal_id = request.GET.get('proposal_id')
    from commissions.models import Proposal
    proposal = Proposal.objects.get(pk = proposal_id)
    return render_to_response(
            'commissions/proposal_comments.html', 
            {'proposal':proposal}, 
            context_instance=RequestContext(request))
