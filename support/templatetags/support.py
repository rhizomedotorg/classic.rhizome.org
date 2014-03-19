from django import template
from django.db import models
from django.core.exceptions import ObjectDoesNotExist


MembershipLevel = models.get_model('support', 'membershiplevel')

register = template.Library()

####MEMBERSHIP LEVELS

class DonationMembershipLevels(template.Node):
    def __init__(self, var_name):
        self.var_name = var_name

    def render(self, context):
        import decimal
        membership_levels = MembershipLevel.objects.filter(is_active=True).exclude(internal_title="user").exclude(internal_title="orgsub")
        
        if membership_levels:
            context[self.var_name] = membership_levels
        return ''

@register.tag
def get_donation_membership_levels(parser, token):
    '''
    just like all the rest, grabs and puts in a variable
    '''
    
    try:
        tag_name = token.split_contents()[-1]
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires arguments" % token.contents.split()[0]
    var_name = tag_name
    return DonationMembershipLevels(var_name)    
    
####MEMBER BENEFITS

class MemberBenefits(template.Node):
    def __init__(self, var_name):
        self.var_name = var_name

    def render(self, context):
        try:
            membership_level = MembershipLevel.objects.get(internal_title="member")
        except ObjectDoesNotExist:
            membership_level = None
                            
        if membership_level:
            member_benefits = membership_level.get_benefits()
        else:
            member_benefits = None
        
        if member_benefits:
            context[self.var_name] = member_benefits
        return ''

@register.tag
def get_member_benefits(parser, token):
    '''
    just like all the rest, grabs and puts in a variable
    '''
    
    try:
        tag_name = token.split_contents()[-1]
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires arguments" % token.contents.split()[0]
    var_name = tag_name
    return MemberBenefits(var_name)
