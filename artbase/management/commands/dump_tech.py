import os
import simplejson as json
from django.conf import settings
from artbase.views import tech_json_data
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Dumps the technologies JSON for the artwork details form"
    def handle(self, *args, **options):
        print "Dumping tech"
        fh = open(os.path.join(settings.STATIC_ROOT, "artbase/data/tech.js"), "w")
        fh.write("var tech_data = %s;" % json.dumps(tech_json_data(), indent=True))
        fh.close()
