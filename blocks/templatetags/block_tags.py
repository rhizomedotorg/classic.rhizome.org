from django import template

from blocks.models import Block
from blocks.nav import PRIMARY_NAV, SUB_NAV


register = template.Library()

@register.simple_tag
def get_text(ident):
    return Block.get_text(ident)

@register.assignment_tag
def assign_text(ident):
    return Block.get_text(ident)

@register.inclusion_tag('fragments/new_navbars.html', takes_context=True)
def get_nav(context, section_name, sub_section_name, html_credits=None):
    sub_nav = []

    if section_name:
        sub_nav = SUB_NAV[section_name]

    return {
        'request': context['request'],
        'STATIC_URL': context['STATIC_URL'],
        'primary_nav': PRIMARY_NAV,
        'sub_nav': sub_nav,
        'section_name': section_name,
        'sub_section_name': sub_section_name,
        'html_credits': html_credits,
    }