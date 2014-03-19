from django.core.management.base import BaseCommand, CommandError
from commissions.models import Cycle
from operator import attrgetter

class Command(BaseCommand):
    """
    tallies approval votes and sets finalists for ranking vote
    """
    def handle(self, *args, **options):
        try:
            cycle_id = args[0]
        except IndexError:
            raise CommandError('Need to pass cycle id')

        try:
            cycle = Cycle.objects.get(pk=int(cycle_id))
        except Cycle.DoesNotExist:
            raise CommandError('Cycle "%s" does not exist' % cycle_id)

        proposals = cycle.get_public_proposals()
        sorted_props = []
        for proposal in proposals:
            proposal.total_votes =  proposal.get_approval_votes_count()
            proposal.yes_votes = proposal.get_is_approved_votes_count()
            proposal.no_votes = proposal.get_not_approved_votes_count()
            proposal.ratio = float(float(proposal.yes_votes) / float(proposal.total_votes))
            
        sorted_props = sorted(proposals, key=attrgetter('ratio'))
        
        x = 0
        finalists = []
        for proposal in sorted_props:
            if proposal.ratio > .415:
                x = x + 1
                print "%s: total votes %s: ratio: %s" % (proposal, proposal.total_votes, proposal.ratio)                
                proposal.rank_vote_finalist = True
                proposal.save()
        print x
