import csv
import os
import datetime

from django.core.management.base import BaseCommand
from django.conf import settings

from artbase.models import ArtworkStub, WorkType

class Command(BaseCommand):
   
    def handle(self, *args, **options):

        with open(os.path.join(settings.MEDIA_ROOT, 'artbase/data/work_to_type.csv'), 'rb') as csvfile:
            work2worktype = csv.reader(csvfile)
            for row in work2worktype:
                if not row[0] == 'work_type' and not row[1] == 'id':
                    print row[0]
                    work_type = WorkType.objects.get(id = row[0])
                    artwork = ArtworkStub.objects.get(id = row[1])                
                    artwork.work_type = work_type

                    type_dict = {
                            "concept_authority":      "Rhizome",
                            "concept_authority_id":   1,
                            "display_string":         "%s" % work_type.work_type,
                            "eff_date":               datetime.datetime.now(),
                            "type":                   "%s" % work_type.work_type,
                            "preferred":              True
                        }

                    document = artwork.get_document()
                    document.work_types = []
                    document.work_types.append(type_dict)
                    document.save()
                    artwork.save()
