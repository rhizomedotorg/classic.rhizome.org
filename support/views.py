from urllib import urlencode
import urllib2
import decimal

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render, render_to_response, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template.context import RequestContext
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.cache import cache_page

from support.forms import *
from support.models import *
from utils.payments import call_authorizedotnet, call_authorizedotnet_capture
from accounts.forms import UserBillingAddressForm, UserShippingAddressForm
from accounts.models import UserAddress
from countries.models import Country, UsState
from utils.helpers import split_by
from accounts.forms import RhizomeUserAuthenticationForm


def individual(request):
    return render(request, 'support/individual.html')

def organizations(request):
    return render(request, 'support/organization.html')

def supporters(request):
    context = RequestContext(request)
    breadcrumb = (("Support", "/support/"),("Supporters", None))  
    return render_to_response(
        "support/supporters.html",
        {"include_section_header": True,
         "supporters":get_current_supporters(),
         "breadcrumb":breadcrumb
        }, 
        context 
    )

def community_campaign(request):
    campaign = CommunityCampaign.objects.current()
    if not campaign and not request.user.is_superuser:
        return redirect('support_donate')

    # shoudlnt be hardcoded, template should be field on campaign
    return render(request, 'support/campaign_2014.html', {})

from django.contrib import messages
from django.contrib.sites.models import get_current_site
from django.shortcuts import render, redirect

from blocks.models import Block
from support.forms import DonationForm, DonationAmountForm


def make_donation(request):
    if CommunityCampaign.objects.current():
        return redirect('campaign')

    donation_amount_form = DonationAmountForm()
        
    if request.method == 'POST':
        donation_amount_form = DonationAmountForm(request.POST)
        
        if donation_amount_form.is_valid():
            response = redirect('confirm_donation')
            response['Location'] += '?amount=%s' % donation_amount_form.cleaned_data['amount']
            return response

    return render(request, 'support/make_donation.html', {
        'form': donation_amount_form
    })

def confirm_donation(request):
    incoming_amount = request.GET.get('amount')

    if not incoming_amount:
        return redirect('support_donate')

    incoming_gift = request.GET.get('gift')
    current_site = get_current_site(request)

    return render(request, 'support/donation_step2.html', {
        'form': DonationForm,
        'paypal': {
            'paypal_url': settings.PAYPAL_POSTBACK_URL,
            'business': settings.PAYPAL_RECEIVER_EMAIL,
            'item_name': 'Donation to Rhizome',
            'return_url': 'http://%s%s' % (current_site.domain, reverse('support_thanks')),
            'cancel_return': 'http://%s/' % current_site.domain,
        },
        'amount': incoming_amount,
        'gift': incoming_gift,
    })

# move to direct to template
def thanks(request): 
    return render(request, 'support/thanks.html')

def format_paypal_response(response):
    lines = response.split('\n')
    status = lines.pop(0)
    data = dict((line.replace('+', ' ').replace('%40', '@').split('=') for line in lines if line))
    return status, data

def thanks_paypal(request):
    tx = request.GET.get('tx')
    if tx:
        postback_dict = dict(cmd = '_notify-synch', at=settings.PAYPAL_IDENTITY_TOKEN, tx=tx)
        postback_reply = urllib2.urlopen(settings.PAYPAL_POSTBACK_URL, urlencode(postback_dict)).read()

        status, data = format_paypal_response(postback_reply)

        if status == 'SUCCESS':
            donation = NewDonation(
                amount = data['payment_gross'],
                first_name = data['first_name'],
                last_name = data['last_name'],
                contact_email = data['payer_email'],
                gift = data['custom'],
                paypal_transaction_id = data['txn_id'],
                paypal_transaction_raw_response = postback_reply,
                payment_method = NewDonation.ELECTRONIC_FUNDS_TRANSFER, 
                via_paypal = True
            ).save()
        else:
            messages.add_message(request, messages.ERROR, 'An error was encountered processing your donation. Please email %s.' % settings.SUPPORT_CONTACT)
        return render(request, 'support/thanks.html')
