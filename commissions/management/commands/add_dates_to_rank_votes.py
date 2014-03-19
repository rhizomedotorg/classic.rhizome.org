from django.core.management.base import BaseCommand, CommandError
from commissions.models import *

class Command(BaseCommand):
    """
    tallies approval votes and sets finalists for ranking vote
    """
    def handle(self, *args, **options):
        rank_votes = RankVote.objects.all()
        for vote in rank_votes:
            if not vote.created:
                 vote.created = vote.proposal.cycle.ranking_vote_start
                 vote.save()
