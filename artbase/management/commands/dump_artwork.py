import csv
import os
import sys
import tldextract

from itertools import groupby
from shutil import copyfile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from artbase.models import ArtworkStub


WORK_TYPES = (
    'Image',
    'Moving Image',
    'Performance',
    'Software',
    'Sound',
    'Website',
    'Installation',
) 

COLUMNS = (
    'Rhizome Archives ID',
    'legacy artbase id',
    'title',
    'artist first name', 
    'artist last name', 
    'byline', 
    'description', 
    'date approved', 
    'URL', 
    'Location', 
    'license_slug', 
    'readme', 
    'tech_details', 
    'created_date', 
    'collective', 
    'other_artists', 
    'tags',
)

def remove_trailing_slash(s):
    if s.endswith('/'):
        s = s[:-1]
    return s

def str_date(d, year_only=False):
    if not d: 
        return d 

    if year_only:
        return d.year
    return d.isoformat(' ').split('.')[0] #MySQL date format

def proper_description(stub):
    return ' '.join(set([s for s in [stub.summary, stub.statement, stub.description] if s]))

def proper_location(stub):
    if stub.location:
        if tldextract.extract(stub.location).subdomain == 'archive':
            return stub.location

        if remove_trailing_slash(stub.location) != remove_trailing_slash(stub.url):
            print '{0} {1} {2}'.format(stub.id, stub.url, stub.location)

    return None

def ca_slug(slug):
    return slug.replace('-', '_')

class Command(BaseCommand):
    help = 'Dumps approved artworks to CSV for Collective Access migration'
    args = 'destination dir'
    archives_ids = {}

    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError('missing argument: destination dir')

        approved_stubs = ArtworkStub.objects.filter(status='approved')
        self.archives_ids = self.build_archives_ids(approved_stubs)

        for wtype in WORK_TYPES:
            stubs = approved_stubs.filter(work_type__work_type=wtype)
            self.write_file(stubs, '%s/%s.csv' % (args[0], wtype.replace(' ', '_').lower()))

        none_type_stubs = approved_stubs.filter(work_type__isnull=True)
        self.write_file(none_type_stubs, '%s/none_type.csv' % args[0])

        self.export_images(approved_stubs, '%s/images/' % args[0])

    def build_archives_ids(self, stubs):
        ids = {}
        for key, values in groupby(stubs.order_by('created'), key=lambda stub: stub.created.year):
            for i, v in enumerate(values):
                ids.update({v.id: 'rza.artwork.%s.%s' % (key, i)})
        return ids 

    def write_file(self, stub_objects, fname):
        f = open(fname, 'w+')
        writer = csv.writer(f)
        writer.writerow(COLUMNS)

        for stub in stub_objects:
            row = (
                self.archives_ids[stub.id],
                stub.id,
                stub.title,
                stub.artist().first_name,
                stub.artist().last_name,
                stub.byline,
                proper_description(stub),
                str_date(stub.created),
                stub.url,
                proper_location(stub),
                ca_slug(stub.license.slug),
                stub.readme,
                stub.tech_details,
                str_date(stub.created_date, year_only=True),
                stub.collective,
                stub.other_artists,
                stub.tags,
            )
            writer.writerow(['' if not s else unicode(s).encode('utf-8') for s in row])

        f.close()
        print 'Successfully wrote %s rows to %s' % (len(stub_objects), f.name)

    def export_images(self, stub_objects, dest_dir):
        try:
            os.stat(dest_dir)
            rmtree(dest_dir)
        except:
            pass

        for stub in stub_objects:
            relative_paths = {
                'featured': str(stub.image_featured),
                'large': str(stub.image_large),
                'medium': str(stub.image_medium),
                'small': str(stub.image_small),
            }

            for key, relative_path in relative_paths.items():
                if 'rhizome_art_default' in relative_path:
                    continue
                    
                file_meta = {
                    'id': self.archives_ids[stub.id],
                    'file_name': os.path.basename(relative_path),
                    'type': key,
                }

                dest_path = dest_dir + '%(type)s/%(id)s/%(id)s_%(file_name)s' % file_meta
                dirname = os.path.dirname(dest_path)

                try: 
                    os.stat(dirname)
                except OSError:
                    os.makedirs(dirname)

                try:
                    copyfile('%s/%s' % (settings.MEDIA_ROOT, relative_path), dest_path)
                except IOError:
                    print 'error copying file: %s' % str(relative_path)

