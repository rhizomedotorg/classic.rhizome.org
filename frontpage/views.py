from django.shortcuts import render
from django.template.context import RequestContext

from blog.models import Post
from exhibitions.models import FrontpageExhibition
from frontpage.models import get_featured_objects_list
from support.models import CommunityCampaign
from threadedcomments.models import ThreadedComment
from utils.template import RhizomePaginator


def frontpage(request):
    exhibition = FrontpageExhibition.objects.current()
    if exhibition:
        return render(request, 'exhibitions/frontpage_exhibition.html', {'exhibition': exhibition})

    blog_posts = Post.objects.published().exclude(staff_blog=True)
    blog_posts_paginator = RhizomePaginator(blog_posts, per_page=10, url='/editorial/')
    blog_posts_paginator.set_current_page(request.GET.get('page'))

    post_list = None
    content = 'editorial'
            
    if request.GET:
        if len(request.GET) > 1 or request.GET.get('page') == None:
            content = request.GET.get('content')
            if content == 'announce':
                post_list = get_latest_announcements(12)
                
            if content == 'discuss':
                from discuss.models import get_discusssion_threads
                post_list = get_discusssion_threads(10)
    
        else:
           fp_paginator = None
           content = 'editorial'

    d = {
        'nobreadcrumb': True,
        'featured_objects': get_featured_objects_list(),
        'comments': ThreadedComment.objects.filter(is_public=True)[:10],
        'content': content,
        'blog_posts_paginator': blog_posts_paginator,
        'post_list': post_list,
    }
                               
    # community campaign modal
    # campaign = CommunityCampaign.objects.current()
    # if campaign:
    #   days_left = campaign.days_left()
    #   if days_left in range(1, 10):
    #     d.update({
    #       'show_campaign_modal': True,
    #       'campaign_days_left': days_left,
    #     })
    
    return render(request, 'frontpage/frontpage.html', d)
