import re
from django import template
from blog.models import Post

register = template.Library()

class PostArchive(template.Node):
    def __init__(self, var_name):
        self.var_name = var_name

    def render(self, context):
        blog_archive_years = Post.objects.dates('publish', 'year', order='DESC')
        blog_archive_months = Post.objects.dates('publish', 'month', order='DESC')
        block_archive_months_split = []
        for year_date in blog_archive_years:
            matching_dates = [month_date for month_date in blog_archive_months if month_date.year == year_date.year]
            block_archive_months_split.append(matching_dates)
        block_archive_breakdown = zip(blog_archive_years,block_archive_months_split)

        if block_archive_breakdown:
            context[self.var_name] = block_archive_breakdown
        return ''


@register.tag
def get_post_archive(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires arguments" % token.contents.split()[0]
    m = re.search(r'as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%s tag had invalid arguments" % tag_name
    var_name = m.groups()[0]
    return PostArchive(var_name)
