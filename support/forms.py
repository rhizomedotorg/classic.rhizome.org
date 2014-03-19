import decimal
import datetime

from django import forms
from django.conf import settings
from django.forms import ModelForm
from django.template import Context
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.template.loader import get_template
from django.template import Context
from django.utils.translation import ugettext_lazy as _

from accounts.models import RhizomeMembership
from support.fields import CreditCardField, CreditCardExpiryField, CreditCardCVV2Field
from support.models import *


def donation_amount_annotation(amount):
    membership_levels = MembershipLevel.objects.filter(is_active=True, donation_level=amount)
    if membership_levels:
        return '$%.2f -- %s' % (amount, membership_levels[0])
    return '$%.2f' % amount

def donation_select_amounts():
    amount_list = [50.00, 100.00, 300.00, 500.00]
    amount_annotations = {}

    for level in MembershipLevel.objects.filter(is_active=True, donation_level__gt=0):
        amount_list.append(level.donation_level)
        amount_annotations[level.donation_level] = str(level)

    sorted_list = sorted(list(set(amount_list)))
    return [('', '')] + [('%.2f' % amount, donation_amount_annotation(amount)) for amount in sorted_list]
        
class DonationAmountForm(forms.Form):
    select_amount = forms.DecimalField(label='Select your donation amount', max_digits=15, decimal_places=2, required=False, widget=forms.Select(choices=donation_select_amounts()))
    custom_amount = forms.DecimalField(label='Or enter your own amount', max_digits=15, decimal_places=2, required=False)
    amount = forms.DecimalField(max_digits=15, decimal_places=2, widget=forms.HiddenInput())
        
class DonationForm(forms.ModelForm):
    card_number = CreditCardField(label='Credit Card Number')
    exp_date = CreditCardExpiryField(label='Expiration Date')
    cvv = CreditCardCVV2Field(label='Card Security Code')

    class Meta:
        model = NewDonation
        fields = ['first_name', 'last_name', 'amount', 'gift', 'contact_email']
