from django.template.loader import get_template
from django.template import Context, Template
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.core.paginator import Paginator
from urlparse import urlparse, parse_qs, urlunparse
from urllib import urlencode

class RhizomePaginator():
    """
    Generic paginator for the Rhizome website. Returns the markup
    for presenting pagination.

    Usage:
       paginator = RhizomePaginator(a_query_set, per_page=5, url=request.get_full_path())
       paginator.set_current_page(request.GET.get("page"))
    """

    def __init__(self, query_set, per_page=10, url=None, custom_page_param=None, anchor_name=None, pages_in_nav=10):
        self.paginator = Paginator(query_set, per_page)
        self.per_page = per_page
        self.pages_in_nav = pages_in_nav
        self.anchor_name = anchor_name

        parsed = urlparse(url)
        hasParams = False
        
        if custom_page_param:
            page_param = custom_page_param
        else:
            page_param = "page"
            
        if parsed.query != "":
            params = list([s for s in parsed.query.split("&")])            
            pageless_url = ''
            for p in params:
                if "%s" % page_param in p:
                    params.remove(p) #we remove page from the url so we can add the correct value in later
                else:
                    if p == params[0]:
                        pageless_url += "%s" % (p)
                    else:
                        pageless_url += "&%s" % (p)
            url = urlunparse((parsed.scheme,
                              None,
                              parsed.path,
                              None,
                              pageless_url,
                              parsed.fragment,))
            parsed = urlparse(url)
            hasParams = (parsed.query != "")
            
#         removed this method using dictionaries and replaced with method above (which uses lists) as previous method caused key values to be  overwritten if key had same name, e.g.  "&models=blog.post&models=announce.event" would cause the key "models" to only "announce.event"
#         # kind lame, Python must have a better way to do this - David
#         if parsed.query != "":
#             params = dict([s.split("=") for s in parsed.query.split("&")])
#             if params.get("page"):
#                 del params["page"]
#             url = urlunparse((parsed.scheme,
#                               None,
#                               parsed.path,
#                               None,
#                               urlencode(params.items()),
#                               parsed.fragment,))
#             parsed = urlparse(url)
#             hasParams = (parsed.query != "")

        if not hasParams:
            self.url = url + "?%s=" % page_param
        else:
            self.url = url + "&%s=" % page_param
        
    def total_pages(self):
        return self.paginator.num_pages
    
    def total_objects(self):
        return self.paginator.count
    
    def set_current_page(self, page, length=None):
        """
        Sets the current page.
        """
        try:
            page = int(page)
        except:
            page = 1
        if not length:
            if page > self.paginator.num_pages:
                page = self.paginator.num_pages
        else:
            if page > length:
                hits = max(1, length - self.orphans)
                self._num_pages = int(ceil(hits / float(self.per_page)))
                if page > self.paginator.num_pages:
                    page = self.paginator.num_pages
        if page < 1:
                page = 1
        self.current_page = page

    def page_range(self, page=None):
        """
        Returns the pages surrounding the page.
        """
        if not page:
            page = self.current_page
        rpage, selected = (page // self.pages_in_nav, self.current_page)

        p = self.paginator.page(rpage+1)
        if not p.has_next:
            start_index = (rpage*self.pages_in_nav)+1
            end_index = self.paginator.num_pages+1
        else:
            if selected != 0:
                if (self.current_page - 5) > 0:
                    start_index = self.current_page - 5
                else:
                    start_index = 1
                    
                end_index = min(self.paginator.num_pages+1, start_index+self.pages_in_nav)
            else:
                start_index = (page-self.pages_in_nav)+1
                end_index = page+1
                
        return range(start_index, end_index)
        
   #  def page_range(self, page=None):
#         """
#         Returns the pages surrounding the page.
#         """
#         if not page:
#             page = self.current_page
#         rpage, selected = (page // self.pages_in_nav, page % self.pages_in_nav)
#         p = self.paginator.page(rpage+1)
#         if not p.has_next:
#             start_index = (rpage*self.pages_in_nav)+1
#             end_index = self.paginator.num_pages+1
#         else:
#             if selected != 0:
#                 start_index = (rpage*self.pages_in_nav)+1
#                 end_index = min(self.paginator.num_pages+1, start_index+self.pages_in_nav)
#             else:
#                 start_index = (page-self.pages_in_nav)+1
#                 end_index = page+1
#         return range(start_index, end_index)


    def object_list(self, page=None):
        """
        Returns a list of objects for a particular page.
        """
        if not page:
            page = self.current_page
        try:
            page = int(page)
        except:
            page = 1
        if page > self.paginator.num_pages:
            page = 1
        p = self.paginator.page(page)
        return p.object_list

    def is_in_last_set(self, page=None):
        """
        Check if we're serving the last set of pages.
        """
        if not page:
            page = self.current_page
        
        return self.page_range(page)[-1] == self.paginator.num_pages

        #return len(self.page_range(page)) < self.pages_in_nav
    
    def is_in_first_set(self, page=None):
        """
        Check if we're serving the first set of pages.
        """
        if not page:
            page = self.current_page
        
        return page < 7
    
    def page_url(self, n):
        """
        Convenience for constructing the page url.
        """
        if self.anchor_name:
            return self.url + str(n) + "#%s" % self.anchor_name
                
        if not self.anchor_name:
            return self.url + str(n)
        
    def start_index(self):
        """
        Returns the 1-based index of the first object on this page,
        relative to total objects in the paginator.
        """
        # Special case, return zero if no items.
        if self.paginator.count == 0:
            return 0
        return (self.per_page * (self.current_page - 1)) + 1

    def end_index(self):
        """
        Returns the 1-based index of the last object on this page,
        relative to total objects found (hits).
        """
        # Special case for the last page because there can be orphans.
        if self.current_page == self.paginator.num_pages:
            return self.total_objects()
        return self.current_page * self.per_page


    def render(self, page=None):
        """
        Render the paginator. Takes a page, uses the current_page
        attribute if page parameter not supplied.
        """
        if not page:
            page = self.current_page
        t = get_template("pagination.html")
        page_range = self.page_range(page)
        pages = [(n, self.page_url(n)) for n in page_range]
        d = {"selected_page": page,
             "pages": pages,
             }
        start_index = page_range[0]
        p = self.paginator.page(page)
        if p.has_previous():
            d["has_previous"] = True
            d["previous_url"] = self.page_url(page-1)
        if p.has_next():
            d["has_next"] = True
            d["next_url"] = self.page_url(page+1)
        if self.is_in_first_set(page):
            d["is_in_first_set"] = True
        else:
            d["first_page"] = 1
            d["first_url"] = self.page_url(1)
        if self.is_in_last_set(page):
           d["is_last_set"] = True
        else:
            d["last_page"] = self.paginator.num_pages
            d["last_url"] = self.page_url(self.paginator.num_pages)
        return t.render(Context(d))
