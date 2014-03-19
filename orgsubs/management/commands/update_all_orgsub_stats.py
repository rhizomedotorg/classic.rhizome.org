import datetime
from collections import defaultdict


from django.core.management.base import BaseCommand
from django.db.models import Count

from hitcount.models import Hit
from orgsubs.models import Organization, MonthlyStatistics

class Command(BaseCommand):
    '''
    calculate visits for orgsubs
    ''' 
    def handle(self, *args, **options):
        self.update_entire_history()

    def update_entire_history(self):
        orgs = Organization.objects.all()
        
        # we need to create a range to break hits down
        # start with oldest hit
        oldest_hit = Hit.objects.all().order_by('created')[1]
        oldest_year = oldest_hit.created.year
        current_year = datetime.datetime.today().year
        
        for org in orgs:
            print org
            orgsub_hits = Hit.objects.filter(orgsub = org)
            stats = {}
            
            for hit in orgsub_hits:
                year = stats.get(hit.created.year, {})            
                month = year.get(hit.created.month, [])
                month.append(hit)                
                year[hit.created.month] = month
                stats[hit.created.year] = year
                
            for stats_key, stats_value in stats.iteritems():
                for stats_value_key, stats_value_value in stats_value.iteritems():
                    month_ip_hits = len([hit for hit in stats_value_value if hit.orgsub_ip == True])
                    month_member_hits = len([hit for hit in stats_value_value if hit.orgsub_member == True]) 
                    monthly_stats = MonthlyStatistics(
                            org_sub = org,
                            year_month = datetime.date(stats_key, stats_value_key, 1),
                            total_visits = len(stats_value_value),
                            ip_visits = month_ip_hits,
                            member_visits = month_member_hits,
                            )   
                    monthly_stats.save()
