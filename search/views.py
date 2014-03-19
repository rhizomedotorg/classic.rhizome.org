from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext

from haystack.query import SearchQuerySet

from utils.template import RhizomePaginator
from search.forms import RhizomeHighlightedModelSearchForm


RESULTS_PER_PAGE = getattr(settings, 'HAYSTACK_SEARCH_RESULTS_PER_PAGE', 20)

def rhizome_search(request, template='search/search.html', load_all=True, form_class=RhizomeHighlightedModelSearchForm, searchqueryset=None, context_class=RequestContext, extra_context=None):
    """
    Custom Search view based off of haystack's basic_search view. Main difference is use of rhizomepaginator
    """
    query = ''
    results = []
    
    if request.GET.get('q'):
        form = form_class(request.GET, searchqueryset=searchqueryset, load_all=load_all)
        
        if form.is_valid():
            query = form.cleaned_data['q']
            results = form.search().order_by('-pub_date')
    else:
        form = form_class(searchqueryset=searchqueryset, load_all=load_all)
    
    search_paginator = RhizomePaginator(results, per_page=RESULTS_PER_PAGE, url=request.get_full_path())
    page = request.GET.get("page")
    search_paginator.set_current_page(request.GET.get("page"))
    
    #breadcrumb = (("Search", None),)
    breadcrumb = None 
     
    context = {
        'form': form,
        'page': page,
        'search_paginator': search_paginator,
        'query': query,
        'breadcrumb': breadcrumb,
    }
    
    if extra_context:
        context.update(extra_context)
    
    return render_to_response(template, context, context_instance=context_class(request))
