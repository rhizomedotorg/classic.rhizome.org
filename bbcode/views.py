from django.shortcuts import render_to_response
from django.template import RequestContext

def help(request, template_name='bbcode/bbhelp.html', extra_context=None):
    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value
    return render_to_response(template_name, context_instance=context)