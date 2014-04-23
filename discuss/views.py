from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import get_current_site
from django.shortcuts import redirect, render
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_page

from discuss.models import DiscussionThread, update_discuss_activity_stream
from discuss.forms import EditDiscussForm
from threadedcomments.models import ThreadedComment 

from advancedmod.utils import moderator
from mailinglists.signals import send_to_discuss_mailing_list

from utils.template import RhizomePaginator


def index(request):
    discussion_threads = DiscussionThread.objects.filter(is_public=True)
    discussion_paginator = RhizomePaginator(discussion_threads, per_page=25, url=request.get_full_path())

    breadcrumb = (('Community', '/community/'), ('Discuss', None))
    
    page = request.GET.get('page')
    if not page or page.isdigit() == False:
        page = 1
    discussion_paginator.set_current_page(int(page))
        
    return render(request, 'discuss/index.html', {
        'include_section_header': True,
        'section_title': 'Rhizome Discuss',
        'section_action': 'submit',     
        'discussion_paginator': discussion_paginator,
        'breadcrumb': breadcrumb
    })

def view_forward(request):
    # exists to combat linkrot?
    id_string = request.GET.get('thread')
    if id_string:
        return redirect('discuss-post-detail', id=''.join([c for c in id_string if c.isdigit()]))
    raise Http404
     
def post_detail(request, id):
    breadcrumb = (('Community', '/community/'), ('Discuss', None))

    if id == unicode(24996): id = '25064' # tom moody redirect
    thread = get_object_or_404(DiscussionThread, pk=id, is_removed=False)

    if not thread.can_view(request.user):
        raise Http404

    if not thread.is_discuss_thread():
        return redirect(thread.content_object)

    return render(request, 'discuss/post_detail.html', {'breadcrumb': breadcrumb, 'thread': thread, 'editable': thread.can_edit(request.user)})

@login_required
def new(request):
    breadcrumb = (('Community', '/community/'), ('Discuss', None))
    form = EditDiscussForm()
    
    if request.method == 'POST':
        form = EditDiscussForm(request.POST)

        if form.is_valid():
            discussion_thread_type = ContentType.objects.get(app_label='discuss', model='discussionthread')
            threadedcomment_type = ContentType.objects.get(app_label='threadedcomments', model='threadedcomment')

            # use placeholder data for now
            thread = DiscussionThread(object_pk=1, content_type=threadedcomment_type, last_comment_id=1)
            thread.save()

            comment = form.save(commit=False)
            comment.content_type = discussion_thread_type
            comment.object_pk = thread.pk
            comment.site = get_current_site(request)
            comment.user = request.user
            comment.save()

            # now we have real data
            thread.object_pk = comment.pk
            thread.last_comment_id = comment.id

            if request.POST['status'] in ['preview']:
                thread.is_public = False
            else:
                thread.is_public = True
            thread.save()

            if not moderator.process(thread, request):
                if thread.is_public:
                    send_to_discuss_mailing_list(thread.content_object, request)
                    update_discuss_activity_stream(thread.content_object, request)

            return redirect('discuss-post-detail', id=thread.id)

    return render(request, 'discuss/new.html', {
        'breadcrumb': breadcrumb,
        'form': form,
    })
    
@login_required 
def edit(request, id):
    breadcrumb = (('Community', '/community/'), ('Discuss', None))

    thread = get_object_or_404(DiscussionThread, pk=id, is_removed=False)
    comment = thread.content_object
    form = EditDiscussForm(instance=comment)
    
    if request.method == 'POST':
        form = EditDiscussForm(request.POST, instance=comment)

        if form.is_valid():
            form.save()

            if request.POST['status'] in ['preview', 'unpublish']:
                thread.is_public = False
            else:
                thread.is_public = True

            thread.save()

            if not moderator.process(thread, request):
                if thread.is_public:
                    send_to_discuss_mailing_list(thread.content_object, request)
                    update_discuss_activity_stream(thread.content_object, request)
                    
            return redirect('discuss-post-detail', id=thread.id)

    if not thread.can_edit(request.user):
        return redirect('discuss-index')

    return render(request, 'discuss/edit.html', {
        'breadcrumb': breadcrumb,
        'form': form,
        'thread': thread
    })
