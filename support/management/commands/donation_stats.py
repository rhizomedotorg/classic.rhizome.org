import csv

from django.core.management.base import BaseCommand, CommandError
from support.models import CommunityCampaign


class Command(BaseCommand):
    help = 'Creates campaign donation CSVs for matplotlib'
    args = 'destination dir'
    archives_ids = {}

    def times_donated(self, donation):
        if donation.user:
            return donation.user.get_profile().get_all_donations().count()
        return 1

    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError('missing argument: destination dir')

        campaign = CommunityCampaign.objects.all()[0]
        donations = campaign.donations.all()

        with open(args[0] + 'data.csv', 'w+') as fp:
            a = csv.writer(fp)
            data = [[d.created, d.amount, self.times_donated(d)] for d in donations]
            a.writerows(data)
