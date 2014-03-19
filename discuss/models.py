import datetime

from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.comments.signals import comment_was_posted
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save

from moderation.anti_spam import check_post_for_spam_via_defensio
from moderation.utils import ModelModerator, moderator
from threadedcomments.models import ThreadedComment

from mailinglists.signals import send_to_discuss_mailing_list


def update_discuss_activity_stream(comment, request):
    from accounts.models import ActivityStream
    activity = ActivityStream()
    activity.user = comment.user 
    activity.created = datetime.datetime.now()
    activity.content_type = ContentType.objects.get_for_model(ThreadedComment)
    activity.object_pk = comment.id
    activity.save()

class DiscussionThread(models.Model):
    content_type = models.ForeignKey(ContentType, related_name='content_type_set_for_%(class)s')
    object_pk = models.IntegerField(max_length=11, db_index=True)
    content_object = generic.GenericForeignKey(ct_field='content_type', fk_field='object_pk')
    last_comment = models.ForeignKey(ThreadedComment)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    is_public = models.BooleanField(db_index=True, default=True)
    is_removed = models.BooleanField(db_index=True, default=False)

    def is_discuss_thread(self): # as opposed to thread attached to posts/artwork etc...
        if isinstance(self.content_object, ThreadedComment) or self == self.content_object:
            return True
        return False

    def started(self):
        if self.is_discuss_thread():
            return self.created
        return self.content_object.created

    def is_blog_thread(self):
        from blog.models import Post
        if isinstance(self.content_object, Post):
            return True
        return False
  
    def __unicode__(self):
        if self.is_discuss_thread():
            return self.content_object.title

        return self.content_object.__unicode__()
            
    def get_absolute_url(self):
        if self.is_discuss_thread():
            return reverse('discuss-post-detail', args=[self.id])

        return self.content_object.get_absolute_url()

    def can_edit(self, user):
        if self.is_discuss_thread():
            margin = datetime.timedelta(days=1)
        
            if user.id == self.content_object.user_id and self.content_object.submit_date > (datetime.datetime.now() - margin):
                return True
        return False

    def can_view(self, user):
        if self.is_public:
            return True

        if self.is_discuss_thread() and user.id == self.content_object.user_id:
            return True
        return False

    def started_by(self):
        if self.is_blog_thread():
            authors = self.content_object.authors.all()
            if authors:
                return authors[0]
            return self.content_object.byline

        if hasattr(self.content_object, 'author'):
            return self.content_object.author

        return self.content_object.user

    class Meta:
        ordering = ['-last_comment__submit_date']

# moderation
class DiscussionThreadModerator(ModelModerator):
    def requires_moderation(self, thread):
        # only moderate threads which are discussion threads
        # as opposed to thread attached to posts/artwork etc...
        if not thread.is_discuss_thread():
            return False

        if not thread.is_public:
            return False

        if thread.content_object.user.get_profile().is_trusted():
            return False
        return True

    def auto_detect_spam(self, thread):
        if check_post_for_spam_via_defensio(thread.content_object.comment):
            return (True, '')
        return (False, '')

    def moderation_queued(self, thread):
        thread.is_public = False

    def moderation_fail(self, thread, request):
        thread.is_public = False
        thread.is_removed = True
        thread.content_object.user.is_active = False
        thread.content_object.user.save()

    def moderation_pass(self, thread, request):
        thread.is_public = True
        thread.content_object.user.get_profile().add_points(3)
        send_to_discuss_mailing_list(thread.content_object, request)
        update_discuss_activity_stream(thread.content_object, request)
        send_mail('Content Approved', self.approved_message_text(thread), settings.DEFAULT_FROM_EMAIL, [thread.content_object.user.email])

    def approved_message_text(self, thread):
        return '%s, your post has been approved by our moderators.\n\nhttp://%s%s' % (
            thread.content_object.user.get_profile(),
            Site.objects.get_current().domain,
            thread.get_absolute_url()
        )

    def admin_info(self, thread):
        return (
            ('author', '<a target="_blank" href="%s">%s</a>' % (thread.content_object.user.get_absolute_url(), thread.content_object.user.get_profile())),
            ('title', thread.content_object.title),
            ('submitted', thread.content_object.submit_date),
            ('body', thread.content_object.comment),
        )

class ThreadedCommentModerator(ModelModerator):
    def requires_moderation(self, comment):
        if comment.user.get_profile().is_trusted():
            return False
        return True

    def auto_detect_spam(self, comment):
        if check_post_for_spam_via_defensio(comment.comment):
            return (True, '')
        return (False, '')

    def moderation_queued(self, comment):
        comment.is_public = False

    def moderation_fail(self, comment, request):
        comment.is_public = False
        comment.is_removed = True
        comment.user.is_active = False
        comment.user.save()

    def moderation_pass(self, comment, request):
        comment.is_public = True
        comment.user.get_profile().add_points(3)
        send_to_discuss_mailing_list(comment, request)
        update_discuss_activity_stream(comment, request)
        send_mail('Content Approved', self.approved_message_text(comment), settings.DEFAULT_FROM_EMAIL, [comment.user.email])

    def approved_message_text(self, comment):
        return '%s, your comment has been approved by our moderators.\n\nhttp://%s%s' % (
            comment.user.get_profile(),
            Site.objects.get_current().domain,
            comment.get_absolute_url()
        )

    def admin_info(self, comment):
        return (
            ('author', '<a target="_blank" href="%s">%s</a>' % (comment.user.get_absolute_url(), comment.user.get_profile())),
            ('title', comment.title),
            ('submitted', comment.submit_date),
            ('body', comment.comment),
        )

moderator.register(DiscussionThread, DiscussionThreadModerator)
moderator.register(ThreadedComment, ThreadedCommentModerator)

# signals
def comment_handler(sender, comment, request, *args, **kwargs):
    discussion_thread_type = ContentType.objects.get(app_label='discuss', model='discussionthread')
    if comment.content_type == discussion_thread_type: # comment on a new or existing discuss thread
        thread = DiscussionThread.objects.get(pk=comment.object_pk)
        thread.last_comment_id = comment.id
        thread.save()
    else: # comment on other site content post/artwork/etc...
        try:
            thread = DiscussionThread.objects.get(content_type=comment.content_type, object_pk=comment.object_pk)
        except DiscussionThread.DoesNotExist:
            thread = DiscussionThread(content_type=comment.content_type, object_pk=comment.object_pk)
        thread.last_comment_id = comment.id
        thread.save()

    comment.title = thread.content_object.title
    comment.save()
    
    if not moderator.process(comment, request):
        send_to_discuss_mailing_list(comment, request)
        update_discuss_activity_stream(comment, request)

comment_was_posted.connect(comment_handler, dispatch_uid='discuss.comment_handler')    
