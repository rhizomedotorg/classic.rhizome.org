from django.core.management.base import BaseCommand, CommandError
from commissions.models import Cycle, RankVote
from operator import attrgetter, itemgetter
from collections import defaultdict


class Command(BaseCommand):
    """
    results in two winning commissions using instant runoff voting method
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

        run_instant_runoff(cycle)

def run_instant_runoff(cycle):
    candidates = cycle.get_rank_vote_finalist_proposals()
    votes = [vote for vote in RankVote.objects.all() if vote.proposal in candidates]
    
    #ballots maps users to all their votes
    ballots = defaultdict(list)
    for vote in votes:
        ballots[vote.user].append(vote)
            
    round_count = 0
    
    print "++++++++++"        
    print "TOTAL USER BALLOTS: %s" % len(ballots)
    print "++++++++++"

    while True:
        #keep the rounds count updated
        round_count +=1
        print "+++++++++++++++++++RUNOFF ROUND %s++++++++++++++++" % round_count
        
        #start by getting the counts
        print "------Vote Counts:" 
        counts = get_counts(ballots, candidates)
        for prop, count in counts.items():
            print "--Proposal:%s, votes:%s " % (prop.title, count)
        print "-----------"
        
        #see if anyone has 50% majority
        print "------Winners this round?" 
        winners = get_winners(ballots, candidates)
        if winners:
            print "--YES!!!!"
            break
        print "NO."
      
        # if no majority, create list of candidates 
        #with least number of 1st place votes 
        #and remove them from candidates list
        print "------Who's Removed this round?:" 
        losers = get_losers(ballots, candidates)
        for loser in losers:
            print "--%s" % loser.title
            candidates.remove(loser)
            
        #keep going until we get someone with 50% maj
    
    #if winner, stop process and declare winner
    print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    print "!!!!!!!!!!!!!!!WE HAVE A WINNER!!!!!!!!!!!!!!!!!!"
    print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"    
    for winner in winners:
        print "!!!!!!!!!%s by %s!!!!!!!!!!" % (winner.title, winner.username)
    print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"    

def get_counts(ballots, candidates):
    """
    Returns the number of votes for each candidate placed first in the
    ballots.
    
    """       
    counts = dict()
    
    #add all candidates to the count dict
    for proposal in candidates:
        counts[proposal] = 0

    #increment through users votes by their rank (i), adding highest ranked prop to counts if that prop not loser
    for voter in ballots:
        i = 0
        for vote in ballots[voter]:
            i += 1
            if int(vote.rank) == i and vote.proposal in candidates:
                counts[vote.proposal] += 1
                break

    return counts

def get_winners(ballots,candidates):
    """
    Returns the winners in the given ballots (lists of candidates), or
    [] if there is no winner.
    
    A winner is a candidate with 50 % or more of the votes, or a
    candidate with as many votes as all the other candidates.
    """

    counts = get_counts(ballots,candidates)

    max_count = max(counts.values())
    num_counts = sum(counts.values())

    potential_winners = [candidate for (candidate, count) in counts.items()
                        if count == max_count]
    
    if max_count >= num_counts/2. or len(potential_winners) == len(counts):
        return potential_winners
    else:
        return []


def get_losers(ballots,candidates):
    """
    Returns the loser(s) of the ballots, i.e. the candidate(s) with the
    fewest voters.
    
    Returns [] if all candidates have the same number of votes.
    """
    
    counts = get_counts(ballots,candidates)
    
    min_count = min(counts.values())
    
    potential_losers = [candidate for (candidate, count) in counts.items()
                       if count == min_count]

    if len(potential_losers) == len(counts):
        return []
    else:
        return potential_losers
   