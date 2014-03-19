from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db.models.base import ModelBase

from moderation.models import QueuedInstance


class Moderator(object):
    def __init__(self):
        self._registry = {}

    def register(self, model_or_iterable, moderation_class):
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            if model not in self._registry:
                self._registry[model] = moderation_class()

    def process(self, obj, request):
        moderation_instance = self._registry.get(obj.__class__)
        if moderation_instance:
            return moderation_instance.process(obj, request)
        return False

class ModelModerator(object):
    def requires_moderation(self, obj):
        return False

    def auto_detect_spam(self, obj):
        return (False, '')

    def moderation_fail(self, obj, request):
        pass

    def moderation_pass(self, obj, request):
        pass

    def moderation_queued(self, obj):
        pass

    def admin_info(self, obj):
        return ()

    def queued_message_text(self, obj):
        return 'Your post has been sent to our staff for moderation.'

    def spam_message_text(self, obj):
        return 'We\'re sorry, but your post did not pass our spam filter.'

    def process(self, obj, request):
        if self.requires_moderation(obj):
            is_spam, reason = self.auto_detect_spam(obj)
            if is_spam:
                self.moderation_fail(obj, request)
                messages.add_message(request, messages.ERROR, self.spam_message_text(obj))
            else:
                QueuedInstance.objects.get_or_create(
                    object_id=obj.id, 
                    content_type=ContentType.objects.get_for_model(obj.__class__), 
                    awaiting_moderation=True)
                self.moderation_queued(obj)
                messages.add_message(request, messages.INFO, self.queued_message_text(obj))
            obj.save()
            return True
        return False

moderator = Moderator()
