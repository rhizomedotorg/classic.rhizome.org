import urllib2
import StringIO
from urlparse import urlparse
import csv
import os 
import datetime

try:
    from BeautifulSoup import BeautifulSoup as Soup
except ImportError:
    Soup = None
        
from PIL import Image

from django.core.management.base import BaseCommand, CommandError
from django.core.files.base import ContentFile
from django.template.defaultfilters import slugify

from django.config import settings
from blog.models import Post, PostImage

class Command(BaseCommand):
    """
    go through old posts without post images, get their image, 
    and store it in a proper place on the site. also make a log
    of any images with 404's
    """
    def handle(self, *args, **options):
        posts = Post.objects.all()
        posts_without_images = [post for post in posts if not post.get_images() and not post.sponsored]
        broken_dict = {}

        for p in posts_without_images:
            print "++++++++++++++++"
            print "++++++++++++++++"
            print "++++++++++++++++"
            print "working on %s" % p.id
            all_urls = p.get_all_images_from_body()
            working_urls = p.get_working_images_from_body()
            broken_urls = p.get_broken_images_from_body()
            print all_urls
            print "working: %s, broken %s" % (working_urls, broken_urls)

            soup = Soup(p.body)

            #get the working url images and save them to server
            for url in working_urls:
                img = urllib2.urlopen(url).read()  
                
                try:
                    image_name = urlparse(url).path.split('/')[-1].replace('%','-')
                    image_ext = image_name.split('.')[-1]
                    image_name = image_name.split('.')[0]
                    image_name = slugify(image_name)
                    image_name = image_name[:25]
                    image_name = image_name +'.'+ image_ext

                    im = Image.open(StringIO.StringIO(img))
                    im.verify()
                    
                    post_image = PostImage()
                    post_image.post = p
                    post_image._width = im.size[0]
                    post_image._height = im.size[1]
                    post_image.title = image_name
                    
                    rhiz_media_url = 'http://media.rhizome.org/blog/%s' % p.id  

                    if rhiz_media_url not in url:
                        # 'downloading and saving image to disk'
                        post_image.image.save(image_name, ContentFile(img), save=False)
                    else:
                        # 'image already on disk, saving path'                    
                        post_image.image = url.replace('http://media.rhizome.org/','')
                    post_image.save()
                     
                    soup_image = soup.findAll('img', {"src": str(url)})[0]
                    
                    # for local testing 
                    soup_image['src'] = "http://localhost:8000/media/%s" % post_image.image
                    
                    #production 
                    #soup_image['src'] = "http://media.rhizome.org/%s" % post_image.image
                
                except Exception, e:
                    broken_urls.append(url)
            
            if broken_urls:
                broken_dict[p.id] = broken_urls

            p.body = soup.prettify()
            p.save()

        writer = csv.writer(open("%s/blog/data/posts_with_broken_images_%s.csv" % (settings.MEDIA_ROOT, datetime.date.today()), "wb"))
        writer.writerow(['POST ID', 'BROKEN URLS']) 
        for key, value in broken_dict.iteritems():
             writer.writerow(["%s" % key,"%s" % value])

        
