from datetime import datetime
from django.core.urlresolvers import reverse
from django.db import models


class FrontpageExhibitionManager(models.Manager):
    def current(self):
    	exhibitions = self.filter(start_time__lte=datetime.now(), end_time__gte=datetime.now())
    	if exhibitions:
    		return exhibitions[0]
    	return None

class FrontpageExhibition(models.Model):
	title = models.CharField(max_length=255)
	slug = models.SlugField()
	description = models.TextField(blank=True, help_text='Metadata only')
	credits = models.TextField('Credits HTML', blank=True)
	image = models.FileField(upload_to='frontpage_exhibitions', blank=True, help_text='If no iframe or video is specified, this is the artwork, otherwise it\'s metadata only.')
	iframe_src = models.URLField(blank=True)
	video_embed_code = models.TextField(blank=True)
	video_aspect_ratio = models.FloatField(null=True, blank=True, help_text='Use decimal format')
	start_time = models.DateTimeField(blank=True, null=True)
	end_time = models.DateTimeField(blank=True, null=True)
	objects = FrontpageExhibitionManager()

	def __unicode__(self):
		return self.title

	def get_absolute_url(self):
		return reverse('frontpage_preview', kwargs={'slug':self.slug})
