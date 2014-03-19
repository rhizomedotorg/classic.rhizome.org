import datetime
from collections import defaultdict


from django.core.management.base import BaseCommand
from django.db.models import Count

from hitcount.models import Hit
from orgsubs.models import Organization, MonthlyStatistics

class Command(BaseCommand):
    '''
    calculate visits for orgsubs and 
    create or update corresponding
    stat object
    ''' 
    def handle(self, *args, **options):
        self.update_monthly_history()

    def update_monthly_history(self):
        orgs = Organization.objects.all()
        
        # we need to create a range to break hits down
        # start with oldest hit
        current_date = datetime.datetime.today()
        
        for org in orgs:
            month_total_visits = 0
            month_ip_visits = 0
            month_member_visits = 0

            orgsub_hits = Hit.objects \
                .filter(orgsub = org) \
                .filter(created__year = current_date.year) \
                .filter(created__month = current_date.month)
            
            if orgsub_hits:
                month_total_visits = len(orgsub_hits)
                month_ip_visits = len([hit for hit in orgsub_hits if hit.orgsub_ip == True])
                month_member_visits = len([hit for hit in orgsub_hits if hit.orgsub_member == True]) 

            try:
                monthly_stats = MonthlyStatistics.objects.get(
                    org_sub = org,
                    year_month = datetime.date(current_date.year, current_date.month, 1),
                    )   
                monthly_stats.total_visits = month_total_visits
                monthly_stats.ip_visits = month_ip_visits 
                monthly_stats.member_visits = month_member_visits
                monthly_stats.save()
                
            except MonthlyStatistics.DoesNotExist:
                    monthly_stats = MonthlyStatistics(
                            org_sub = org,
                            year_month = datetime.date(current_date.year, current_date.month, 1),
                            total_visits = month_total_visits,
                            ip_visits = month_ip_visits,
                            member_visits = month_member_visits,
                        )  
                    monthly_stats.save()
