from django.core.management.base import BaseCommand, CommandError
from blog.models import *
import os

class Command(BaseCommand):
    """
    create thumbnail for blog posts
    """
    def handle(self, *args, **options):
        post_images = PostImage.objects.all()
        for image in post_images:
            if image.image and not image.thumbnail:
                if os.path.exists(image.image.path):
                    from easy_thumbnails.files import get_thumbnailer
                    thumbnail_options = dict(size=(100, 75), crop=True)
                    try:
                        thumbnail = get_thumbnailer(image.image).get_thumbnail(thumbnail_options)        
                        image.thumbnail = thumbnail
                        image.save()
                    except:
                        pass
