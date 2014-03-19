from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import pre_delete

import moderation.utils


class QueuedInstance(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    awaiting_moderation = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created']

    def moderation_instance(self):
        return moderation.utils.moderator._registry.get(self.content_type.model_class())

    def moderate(self, request, fail=False):
        moderation_instance = self.moderation_instance()

        if fail:
            moderation_instance.moderation_fail(self.content_object, request)
        else:
            moderation_instance.moderation_pass(self.content_object, request)

        self.content_object.save()
        self.delete()

    def admin_info(self):
        return {
            'obj': self, 
            'obj_type': self.content_type.model_class()._meta.verbose_name,
            'info': self.moderation_instance().admin_info(self.content_object)
        }

# signals
def delete_queued_instances(sender, instance, **kwargs):
    # replicate cascade-style delete fucntionality for queued instances 
    try:
        queued_instances = QueuedInstance.objects.filter(
            object_id=instance.pk, 
            content_type=ContentType.objects.get_for_model(sender)
        ).delete()
    except:
        pass
pre_delete.connect(delete_queued_instances, dispatch_uid='moderation.delete_queued_instances')    
