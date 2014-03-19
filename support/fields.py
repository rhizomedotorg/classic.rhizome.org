#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import date
from calendar import monthrange

from django import forms
from django.utils.translation import ugettext as _

from creditcard import verify_credit_card

class CreditCardField(forms.CharField):
    """
    Form field for checking out a credit card.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 20)
        super(CreditCardField, self).__init__(*args, **kwargs)

    def clean(self, value):
        """
        Raises a ValidationError if the card is not valid
        and stashes card type.
        """
        self.card_type = verify_credit_card(value)
        if self.card_type is None:
            raise forms.ValidationError("Invalid credit card number.")
        return value


# Credit Card Expiry Fields from:
# http://www.djangosnippets.org/snippets/907/
class CreditCardExpiryWidget(forms.MultiWidget):
    """MultiWidget for representing credit card expiry date."""
    def decompress(self, value):
        if value:
            return [value.month, value.year]
        else:
            return [None, None]

    def format_output(self, rendered_widgets):
        html = u' / '.join(rendered_widgets)
        return u'<span style="white-space: nowrap">%s</span>' % html


class CreditCardExpiryField(forms.MultiValueField):
    EXP_MONTH = [(x, x) for x in xrange(1, 13)]
    EXP_YEAR = [(x, x) for x in xrange(date.today().year,
                                       date.today().year + 15)]

    default_error_messages = {
        'invalid_month': u'Enter a valid month.',
        'invalid_year': u'Enter a valid year.',
    }

    def __init__(self, *args, **kwargs):
        errors = self.default_error_messages.copy()
        if 'error_messages' in kwargs:
            errors.update(kwargs['error_messages'])

        fields = (
            forms.ChoiceField(
                choices=self.EXP_MONTH,
                error_messages={'invalid': errors['invalid_month']}),
            forms.ChoiceField(
                choices=self.EXP_YEAR,
                error_messages={'invalid': errors['invalid_year']}),
        )

        super(CreditCardExpiryField, self).__init__(fields, *args, **kwargs)
        self.widget = CreditCardExpiryWidget(widgets=[fields[0].widget,
                                                      fields[1].widget])

    def clean(self, value):
        exp = super(CreditCardExpiryField, self).clean(value)
        if date.today() > exp:
            raise forms.ValidationError(
                "Invalid Expiration Date.")
        return exp

    def compress(self, data_list):
        if data_list:
            if data_list[1] in forms.fields.EMPTY_VALUES:
                error = self.error_messages['invalid_year']
                raise forms.ValidationError(error)
            if data_list[0] in forms.fields.EMPTY_VALUES:
                error = self.error_messages['invalid_month']
                raise forms.ValidationError(error)
            year = int(data_list[1])
            month = int(data_list[0])
            # find last day of the month
            day = monthrange(year, month)[1]
            return date(year, month, day)
        return None


class CreditCardCVV2Field(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 4)
        super(CreditCardCVV2Field, self).__init__(*args, **kwargs)