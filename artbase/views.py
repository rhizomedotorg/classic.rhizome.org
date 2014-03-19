import os
import math              

from django.db import connection
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import Http404
from django.template.context import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.forms.util import ErrorList
from django.utils.html import strip_tags
from django.views.decorators.cache import cache_page

import simplejson as json
from couchdb.client import *

from tagging.models import Tag, TaggedItem
from utils.helpers import split_by, remove_duplicates_and_preserve_order, browse_helper
from utils.template import RhizomePaginator
from utils.helpers import truncate_text
from artbase.forms import BaseArtworkForm, ArtworkMediaForm, ArtworkDetailsForm, ArtworkLicenseAgreementForm, ApproveTagsForm, sync_document_and_stub
from artbase.models import *
from accounts.decorators import membership_required
from orgsubs.models import is_ip_org_sub

server = Server("http://localhost:5984")
try:
    db = server["artbase"]
except:
    pass

ARTBASE_DESCRIPTION = '''Founded in 1999, the Rhizome ArtBase is an online archive of new media art containing some %s art works, and growing. The ArtBase encompasses a vast range of projects by artists all over the world that employ materials such as software, code, websites, moving images, games and browsers to aesthetics and critical ends. We welcome submissions to the ArtBase; they are reviewed by our curatorial staff on a monthly basis. <a href="/artbase/about/">Read More &raquo;</a>
'''

ARTBASE_SECTIONS = (
    ("featured", "Featured"),
    ("exhibitions", "Member Exhibitions"),
    ("essays", "Essays"),
    ("submit", "Submit"),
)

# ==============================================================================
# Helper Functions
# ==============================================================================

def tech_json_data():
    qr = Technology.objects.all()
    result = {}
    for tech in qr:
        if tech.category and not result.get(tech.category):
            result[tech.category] = {}
        if tech.type and not result[tech.category].get(tech.type):
            if tech.version:
                result[tech.category][tech.type] = {}
            else:
                result[tech.category][tech.type] = tech.id
        if tech.version:
            result[tech.category][tech.type][tech.version] = tech.id
    return result

def all_artbase_works(start_date=None, end_date=None, limit=300, all=False):
    if start_date and end_date:
        return ArtworkStub.objects.filter(status="approved").filter(created__range=(start_date, end_date)).order_by("-created_date").exclude(needs_repair=True)
    if start_date:
        return ArtworkStub.objects.filter(status="approved").filter(created__gte=start_date).order_by("-created_date").exclude(needs_repair=True)
    if end_date:
        return ArtworkStub.objects.filter(status="approved").filter(created__lte=datetime.datetime.now()).order_by("-created_date").exclude(needs_repair=True)
    if all:
        return ArtworkStub.objects.filter(status="approved").order_by("-created_date").exclude(needs_repair=True)
    else:
        return ArtworkStub.objects.filter(status="approved").order_by("-created_date").exclude(needs_repair=True)[:300]


def artbase_count():
    return ArtworkStub.objects.filter(status="approved").count()

def frontpage_collections():
    return Collection.objects.filter(live=1).order_by('-created')[:6]

def featured_works():
    fs = None
    try:
        fs = FeaturedSet.objects.get(current=1)
    except:
        pass
    if not fs:
        return latest_additions()
    else:
        return fs.artworks.all()


def latest_essays():
    from blog.models import Post
    return Post.objects.published().filter(artbase_essay=1).order_by('-publish')


def latest_member_exhibitions():
    return MemberExhibition.objects.filter(live=1).exclude(image = "artbase/exhibition_images/rhizome_exhibition_default.png").order_by('-time_opened')


def users_exhibitions(user, authenticated=False):
    uxs = MemberExhibition.objects.filter(user=user)
    if not authenticated:
        return uxs.filter(live=1) or []
    return uxs


def featured_in(artworkstub, limit=10):
    exs =  [x.exhibition for x in MemberExhibitionArtwork.objects.filter(artwork=artworkstub).exclude(exhibition__image="artbase/exhibition_images/rhizome_exhibition_default.png")[:limit] if x.exhibition.live ==1]
    exs = [ex for ex in exs if os.path.exists(ex.image.path)]
    return exs   

def similar_works(artworkstub, limit=10):
    tags = artworkstub.tags.filter(approved=True)
    similar = []
    limit = min(limit, len(tags))
    for i in range(limit):
        tag = tags[i]
        x = tag.concept.conceptitem_set.all()[:1]
        if len(x) > 0:
            similar.append(x[0].content_object)
    return similar


def similar_exhibitions(exhibition, limit=10):
    tags = exhibition.tags
    similar = []
    limit = min(limit, len(tags))
    for i in range(limit):
        tag = tags[i]
        x = tag.concept.conceptitem_set.all()[:1]
        if len(x) > 0:
            similar.append(x[0].content_object)
    return similar


def most_curated(limit=12):
    cursor = connection.cursor()
    cursor.execute("SELECT artwork_id, COUNT(id) FROM artbase_memberexhibitionartwork GROUP BY artwork_id ORDER BY COUNT(id) DESC")
    results = []
    for row in cursor.fetchmany(limit):
        id, count = row
        results.append(ArtworkStub.objects.get(pk=id))
    return results


def most_saved(limit=12):
    cursor = connection.cursor()
    cursor.execute("SELECT artworkstub_id, COUNT(id) FROM accounts_rhizomeuser_saved_artworks GROUP BY artworkstub_id ORDER BY COUNT(id) DESC")
    results = []
    for row in cursor.fetchmany(limit):
        id, count = row
        results.append(ArtworkStub.objects.get(pk=id))
    return results

def random_most_saved():
    from random import choice
    try:
        return choice(most_saved())
    except IndexError:
        return None

def random_works(limit=12):
    cursor = connection.cursor()
    cursor.execute("SELECT id from artbase_artworkstub WHERE image_small != 'artbase/images/rhizome_art_default.png' AND needs_repair != 1 ORDER BY RAND() LIMIT %s" % limit)
    results = []
    for row in cursor.fetchmany(limit):
        work_id = row[0]
        results.append(ArtworkStub.objects.get(pk=work_id))
    return results

def random_artbase_works(limit=None):
    if limit:
        results = ArtworkStub.objects.filter(status="approved").exclude(status="deleted").exclude(image_small = 'artbase/images/rhizome_art_default.png').exclude(image_small = None).exclude(needs_repair=True).order_by('?')[:limit]  
        results = [x for x in results if os.path.exists(x.image_small.path)]
    else:
        results = ArtworkStub.objects.filter(status="approved").exclude(status="deleted").exclude(image_small = 'artbase/images/rhizome_art_default.png').exclude(image_small = None).exclude(needs_repair=True).order_by('?')[:12]       
        results = [x for x in results if os.path.exists(x.image_small.path)]

    return results

def latest_additions(limit=12):
    return ArtworkStub.objects.filter(status="approved").exclude(image_small = 'artbase/images/rhizome_art_default.png').order_by('-approved_date')[:limit]

def recently_archived(limit=12):
    return ArtworkStub.objects.filter(status="approved").filter(location_type="cloned").exclude(image_small = 'artbase/images/rhizome_art_default.png') \
        .order_by('-approved_date')[:limit]

def random_recently_archived():
    from random import choice
    try:
        return choice(recently_archived())
    except IndexError:
        return None


def work_json_data(artworkstub, to_json=True, no_tags=False):
    try:
        d = {"work_id": artworkstub.id,
         "title": artworkstub.title,
         "artist": artworkstub.byline or "Unknown",
         "artist_url": artworkstub.artist().get_profile().get_absolute_url(),
         "created": str(artworkstub.created_date),
         "image": "%s%s" % (settings.MEDIA_URL, artworkstub.image_featured.__unicode__()),
         "url": artworkstub.view_url(),
         }

    except:
        # in case artist doesn't have get_profile method b/c of user obj error
        d = {"work_id": artworkstub.id,
         "title": artworkstub.title,
         "artist": artworkstub.byline or "Unknown",
         "artist_url": None,
         "created": str(artworkstub.created_date),
         "image": "%s%s" % (settings.MEDIA_URL, artworkstub.image_featured.__unicode__()),
         "url": artworkstub.view_url(),
         }

    if not no_tags:
        d["tags"] = [{"name":tag.name, "url": tag.url()} for tag in artworkstub.get_tags()]
    if not to_json:
         return d
    return json.dumps(d, indent=2)

def works_json_data(artworks, no_tags=False):
    """
    Generate JSON data so JavaScript on page has access to artwork information.
    """
    return json.dumps([work_json_data(artwork, to_json=False, no_tags=no_tags)
                       for artwork in artworks], indent=2)

def users_exhibition_json_data(ux, to_json=True):
    """
    Takes a list of a user's exhibition and returns JSON.
    """
    d = {"id": ux.id,
         "title": ux.title}
    if not to_json:
        return d
    return json.dumps(d, indent=2)


def artbase_approved_tags():
    ctype = ContentType.objects.get(app_label="artbase", model="artworkstub")
    tag_ids = ", ".join([str(t['tag_id']) for t in TaggedItem.objects.filter(content_type__pk=ctype.id,approved=True).values("tag_id").distinct()])
    return Tag.objects.extra(where=["id in (%s)" % tag_ids]).order_by("name")

def users_exhibitions_json_data(uxs):
    return json.dumps([users_exhibition_json_data(ux, False) for ux in uxs], indent=2)

# ==============================================================================
# Views
# ==============================================================================

#def index(request):
#    """
#    Serves the main index page.
#    """
#    context = RequestContext(request)
#    return HttpResponseRedirect("featured")

def about(request):
    context = RequestContext(request)    
    breadcrumb = (('ArtBase', '/artbase/'), ('About', None))
    about_artbase = AboutArtbase.objects.get(pk=1)
    d = {
        'documents': ArtbaseDocument.objects.all(),
        'about_artbase': about_artbase,
        'breadcrumb': breadcrumb,
        'artbase_count': artbase_count()
      }
    
    return render_to_response('artbase/about.html', d,context)

def policy(request):
    context = RequestContext(request)
    cm_policy = CollectionManagementPolicy.objects.get(pk=1)
    aa_policy = ArtistAgreement.objects.get(pk=1)
    breadcrumb = (("Artbase","/artbase/"),("Policy",""))
    d = {"cm_policy":cm_policy.policy,
        "aa_policy":aa_policy.policy,
        "breadcrumb":breadcrumb
    }
    
    return render_to_response("artbase/policy.html", d, context)

def featured(request):
    """
    Serves the featured content page.
    """
    context = RequestContext(request)
    breadcrumb = (('ArtBase', '/artbase/'),)
    featured_artworks = featured_works()
    flash_msg = request.GET.get("flash")

    try:
        featured_artwork = featured_artworks[0]
    except IndexError:
        featured_artwork = None

    d = {
         "include_section_header": True,
         "artbase_section_header": True,
         "artbase_section_description": ARTBASE_DESCRIPTION % artbase_count(),         
         "featured_artwork": featured_artworks[0] if 0 < len(featured_artworks) else None,
         "featured_artworks": featured_artworks,
         "artbase_json_data": { "featured_works": works_json_data(featured_artworks) },
         "exhibitions": latest_member_exhibitions()[:3],
         "favorite": random_most_saved(),
         "archived": random_recently_archived(),
         "frontpage_collections": frontpage_collections(),
         "flash_msg": flash_msg,
         'breadcrumb': breadcrumb
    }

    return render_to_response("artbase/featured_new.html", d, context)

def featured_list(request, list_type):
    context = RequestContext(request)
    works = []
    if list_type == "latest-additions":
        works = latest_additions()
    elif list_type == "most-curated":
        works = most_curated()
    elif list_type == "most-saved":
        works = most_saved()
    elif list_type == "random-works":
        works = random_works()
    d = {"list_type": list_type,
         "list_works": works}
    return render_to_response("artbase/featured_list.html", d, context)


def featured_fragment(request, id):
    context = RequestContext(request)
    featured_artworks = featured_works()
    featured_artwork = ArtworkStub.objects.get(pk=id)
    d = {"featured_artwork": featured_artwork,
         "featured_artworks": featured_artworks}
    return render_to_response("artbase/featured_work.html", d, context)

def member_exhibitions(request):
    """
    Serves the member exhbitions page.
    """
    context = RequestContext(request)

    exhibition_paginator = RhizomePaginator(latest_member_exhibitions(),
                                            per_page=3,
                                            url=request.get_full_path())
    exhibition_paginator.set_current_page(request.GET.get("page"))
    breadcrumb = (('ArtBase', '/artbase/'), ('Member Exhibitions', None))

    d = {"include_section_header": True,
         "section_title": "Rhizome Member Exhibitions",
         "section_action": "new",
         "exhibition_paginator": exhibition_paginator,
         'breadcrumb': breadcrumb
       }
    return render_to_response("artbase/member_exhibitions.html", d, context)


def can_edit_exhibition(request, id):
    exhibition = MemberExhibition.objects.get(pk=id)
    if (request.user == exhibition.user) or request.user.is_staff:
        return exhibition
    return False


def can_view_exhibition(request, id):
    try:
        exhibition = MemberExhibition.objects.get(pk=id)
    except:
        exhibition = None
    
    if exhibition:
        if (request.user == exhibition.user) or request.user.is_staff or exhibition.live == True:
            return exhibition
        else:
            return None
    else:
        return None

def view_member_exhibition(request, id):
    context = RequestContext(request)
    exhibition = can_view_exhibition(request, id)
        
    if request.GET.get("flash"):
        flash_msg = True
    else:
        flash_msg = False
        
    if not exhibition:
        return HttpResponseRedirect(reverse(featured))
        
    d = {"is_users_exhibition": request.user == exhibition.user,
         "include_section_header": True,
         "exhibition": exhibition,
         "grouped": list(split_by(exhibition.works(), 3, pad=True)),
         "flash_msg":flash_msg
         #"similar_exhibitions": similar_exhibitions(exhibition)
         }
    return render_to_response("artbase/view_member_exhibition.html", d, context)


@login_required
@membership_required
def new_member_exhibition(request):
    from artbase.forms import MemberExhibitionForm

    title = request.GET.get("title") or "Untitled"
    work_id = request.GET.get("id")
    context = RequestContext(request)
    artworks = []

    if work_id:
        artworks.append(ArtworkStub.objects.get(pk=work_id))

    initial = {"title": title,
               "subtitle": "",
               "artworks": " ".join([str(artwork.id) for artwork in artworks])}

    d = {"form": MemberExhibitionForm(initial=initial),
         "page_title": "New Exhibition",
         "exhibition_id": None,
         "artworks": artworks}
    
    return render_to_response("artbase/edit_member_exhibition.html", d, context)


def to_artworks(astr):
    if not astr:
        return []
    return [ArtworkStub.objects.get(pk=int(s.strip())) for s in astr.split(" ")]


@login_required
@membership_required
def preview_member_exhibition(request, id):
    context = RequestContext(request)
    exhibition = can_edit_exhibition(request, id)
    
    if not exhibition:
        return HttpResponseRedirect(reverse(featured))
    d = {"is_users_exhibition": request.user == exhibition.user,
         "flash_msg": "preview_exhibition",
         "include_section_header": True,
         "exhibition": exhibition,
         "grouped":list(split_by(exhibition.works(), 3, pad=True)),
         #"similar_exhibitions": similar_exhibitions(exhibition)
         }
    return render_to_response("artbase/view_member_exhibition.html", d, context)


@login_required
@membership_required
def edit_member_exhibition(request, id=None):
    context = RequestContext(request)
    from artbase.forms import MemberExhibitionForm    
    
    try:
        instance = id and MemberExhibition.objects.get(pk=id)
    except:
        raise Http404
        
    artworks = []

    if instance and not can_edit_exhibition(request, id):
        return HttpResponseRedirect(reverse(featured))

    if instance:
        artworks = [x for x in instance.works()]
        initial = {"artworks": " ".join([str(x.id) for x in instance.works()])}
        form = MemberExhibitionForm(request.POST or None, request.FILES or None, instance=instance, initial=initial)
    else:
        form = MemberExhibitionForm(request.POST or None, request.FILES or None,)
    
    if request.method == "POST":
        if form.is_valid():
            exhibition = form.save(commit=False)
            
            if not request.POST.get("delete"):
                exhibition.user = request.user
                exhibition_artworks = [x for x in exhibition.memberexhibitionartwork_set.all() if x.artwork.status != "deleted"]
                exhibition.save()

                if form.cleaned_data.get("artworks"):
                    artworks = to_artworks(form.cleaned_data["artworks"])
                    
                    # update user's exhibition artwork positions, create the exhibition artwork if necessary
                    for i in range(len(artworks)):
                        artwork = artworks[i]
                        # from irc, select the matching item out of a list
                        c = next((x for x in exhibition_artworks if x.artwork == artwork), None)
                        
                        if c:
                            c.position = i
                        else:
                            c = MemberExhibitionArtwork(artwork=artwork,
                                                        exhibition=exhibition,
                                                        note="",
                                                        position=i)
                        c.save()
                        
                if request.POST.get("publish"):
                    exhibition.live = True
                    exhibition.time_opened = datetime.datetime.now()
                    exhibition.save()
                
                if request.POST.get("browse"):
                    return HttpResponseRedirect("/artbase/browse/")
                    
                if request.POST.get("save_draft") or request.POST.get("update"):
                    return HttpResponseRedirect("/artbase/exhibitions/edit/%s" % exhibition.id)

                if request.POST.get("view"):
                    return HttpResponseRedirect("/artbase/exhibitions/view/%s" % exhibition.id)
            
                if request.POST.get("publish"):
                    #return HttpResponseRedirect(reverse(preview_member_exhibition, args=[exhibition.id]))
                    exhibition.user.get_profile().add_points_for_object(exhibition)
                    return HttpResponseRedirect("/artbase/exhibitions/view/%s?flash=published" % exhibition.id)
                
                if request.POST.get("preview"):
                    return HttpResponseRedirect("/artbase/exhibitions/preview/%s" % exhibition.id)
                    #return HttpResponseRedirect(reverse(preview_member_exhibition, args=[exhibition.id]))

            else:
                    #return HttpResponseRedirect(reverse(delete_member_exhibition, args=[exhibition.id]))
                    return HttpResponseRedirect("/artbase/exhibitions/delete/%s" % exhibition.id)

    d = {"exhibition": instance,
         "exhibition_id": (instance and instance.id) or None,
         "page_title": "Edit Exhibition",
         "form": form,
         "artworks": artworks}

    return render_to_response("artbase/edit_member_exhibition.html", d, context)


@login_required
@membership_required
def edit_member_exhibition_add_work(request, id):
    """
    View that support the user exhibition widget for quickly
    adding artworks to an exhibition.
    """
    exhibition = MemberExhibition.objects.get(pk=id)
    
    if exhibition is None:
        raise Http404
    if request.user != exhibition.user:
        raise Http404

    work_id = request.POST.get("artwork_id")
    if request.POST and work_id:
        work = ArtworkStub.objects.get(pk=work_id)
        if not exhibition.has_work(work):
            new_exhibition_artwork = MemberExhibitionArtwork(artwork=work,
                                                             exhibition=exhibition,
                                                             note="",
                                                             position=len(exhibition.works()))
            new_exhibition_artwork.save()
        return HttpResponseRedirect(reverse(edit_member_exhibition, args=[exhibition.id]))
    else:
        raise Http404


@login_required
@membership_required
def edit_member_exhibition_remove_work(request, id):
    work_id = request.GET.get("work_id")
    exhibition = MemberExhibition.objects.get(pk=id)
    
    if exhibition is None:
        raise Http404
    if request.user != exhibition.user:
        raise Http404

    if request.GET and work_id:
        work = ArtworkStub.objects.get(pk=work_id)
        if exhibition.has_work:
            exhibition.remove(work)
        return HttpResponseRedirect(reverse(edit_member_exhibition, args=[exhibition.id]))
    else:
        raise Http404


@login_required
@membership_required
def delete_member_exhibition(request, id):
    exhibition = MemberExhibition.objects.get(pk=id)
    if exhibition and request.user == exhibition.user:
        exhibition.delete()
        return redirect('member_exhibitions')
    else:
        raise Http404


def can_edit_artwork(request, id):
    """
    Returns False if the user is not staff, or the artwork's original creator
    or the artwork has been deleted. Otherwise returns the artwork
    """
    work = ArtworkStub.objects.get(pk=id)
    
    try:
        if not work or work.status == "deleted":
            return False
        elif (request.user == work.user) or request.user.is_staff:
            return work
        return False
    except User.DoesNotExist:
        if  request.user.is_staff:
            return work
        else:  
            return False

def artwork_forward(request, id=None):
    if id:
        return HttpResponseRedirect("/artbase/artwork/%s" % id)
    elif request.GET and not id:
         for key,value in request.GET.items():
            id = key
            return HttpResponseRedirect("/artbase/artwork/%s" % id)
    else:
        return HttpResponseRedirect("/artbase/")

def object_forward(request):
    artwork_id = request.GET.get('o')
    if artwork_id:
        return HttpResponseRedirect("/artbase/artwork/%s" % artwork_id)
    else:
        return HttpResponseRedirect("/artbase/")        

def artwork(request, id, extra_context=None):
    # serves the single artwork page
    context = RequestContext(request)
    artwork = get_object_or_404(ArtworkStub, pk=id)

    if artwork.status == 'deleted':
        return HttpResponseRedirect('/artbase/')

    if artwork is None:
        raise HttpResponseRedirect(reverse(featured))

    try:
        if not artwork.user.is_active:
            if artwork.status not in ['approved', 'to_consider']:
                return HttpResponseRedirect('/artbase/')
    except User.DoesNotExist:
        pass

    is_orgsub_ip = is_ip_org_sub(request.META['REMOTE_ADDR'])
    exs = featured_in(artwork, limit=10)
    
    d = {
        'include_section_header': True,
        'artwork': artwork,
        'tags': artwork.tags,
        'exhibitions': list(split_by(exs, 3, pad=True)),
        'exhibitions_count': len(exs),
        'saved_by': artwork.get_saved_by(),
        'related_works': artwork.get_related_works(),
        'is_orgsub_ip': is_orgsub_ip,
        'artbase_json_data': {'artwork': work_json_data(artwork)}
    }

    if extra_context:
        d.update(extra_context)

    if artwork.status != 'approved':
        breadcrumb = (('Community', '/community/'), ('Portfolios', None))
        d['breadcrumb'] = breadcrumb
        
    is_authenticated = request.user.is_authenticated()
    if is_authenticated:
        d['is_authenticated'] = True
        uxs = users_exhibitions(request.user, is_authenticated)
        d['artbase_json_data']['users_exhibitions'] = users_exhibitions_json_data(uxs)

    if can_edit_artwork(request, id):
        d['can_edit_artwork'] = True

    if artwork.status != 'approved':
        return render_to_response('artbase/portfolio_artwork.html', d, context)
    else:
        return render_to_response('artbase/artbase_artwork.html', d, context)


@login_required
def preview_artwork(request, id):   
    extra_context = {
        'preview_mode': True,
        'flash_msg': 'preview_artwork',
    }
    return artwork(request, id, extra_context)
    

def submit(request):
    """
    Handle the submission of new artworks from artists
    """
    context = RequestContext(request)
    breadcrumb = (('ArtBase', '/artbase/'), ('Submit', None))

    if request.method == "POST":
        form = BaseArtworkForm(request.POST)
        if form.is_valid():
            new_artworkstub = form.save(commit=False)
            new_artworkstub.user = request.user
            new_artworkstub.save()
#            return HttpResponseRedirect(reverse(edit_artwork_base, args=[new_artworkstub.id]))#reverse lookups adding weirdness in url...
            return HttpResponseRedirect("/artbase/artwork/%s/edit/base" % new_artworkstub.id)

    else:
        form = BaseArtworkForm()
    d = {"include_section_header": True,
         "section_title": "Let's say I submit, then what?",
         "form": form,
         "form_path": "artbase/forms/artwork_base.html",
         "form_type": "base",
         'breadcrumb': breadcrumb
      }
    return render_to_response("artbase/submit.html", d, context)


@login_required
def submitted(request):
    """
    View for handling successfully submitted artworks.
    """
    context = RequestContext(request)
    return render_to_response("artbase/submitted.html", {}, context)


@login_required
def edit_artwork(request, id):
    """
    Handles the editing of existing artworks
    """        
    if not id:
        return HttpResponseRedirect(reverse(featured))
        
    #return HttpResponseRedirect(reverse(edit_artwork_base, args=[id]))
    return HttpResponseRedirect("/artbase/artwork/%s/edit/base" % id)

@login_required
def edit_artwork_base(request, id):        
    context = RequestContext(request)
    work = can_edit_artwork(request, id)
    agree_to_agreement_error = False

    if not work:
        return HttpResponseRedirect(reverse(featured))

    if request.method == "POST":
    
        if request.POST["status"] == "delete":
            return HttpResponseRedirect(reverse(delete_artwork, args=[id]))
            
        form = BaseArtworkForm(request.POST, instance=work)
        
        if form.is_valid():
            instance = form.save(commit=False)
            instance.description = strip_tags(instance.description)
            instance.statement = strip_tags(instance.statement)
            instance.summary = strip_tags(instance.summary)            
            instance.save()
            document, stub = sync_document_and_stub(instance.get_document(), instance)
            document.save()

            if request.POST["status"] == "publish":
                if instance.agree_to_agreement:
                    instance.submitted_date = datetime.datetime.now()
                    instance.status = "awaiting"
                    instance.save()
                    return HttpResponseRedirect("%s" % instance.view_url())
                else:
                    agree_to_agreement_error = True

            if request.POST["status"] == "preview":
                #return HttpResponseRedirect(reverse(preview_artwork, args=[instance.id]))
                return HttpResponseRedirect("/artbase/artwork/%s/preview" % instance.id)

            if request.POST["status"] == "view":
                #return HttpResponseRedirect(reverse(preview_artwork, args=[instance.id]))
                return HttpResponseRedirect("/artbase/artwork/%s/" % instance.id)

            if request.POST["status"] == "save draft" or request.POST["status"] == "update":
                #return HttpResponseRedirect(reverse(edit_artwork_base, args=[instance.id]))
                return HttpResponseRedirect("/artbase/artwork/%s/edit/base" % id)
    else:
        form = BaseArtworkForm(instance=work)
        
    d = {"include_section_header": True,
         "section_title": "Let's say I submit, then what?",
         "form": form,
         "form_path": "artbase/forms/artwork_base.html",
         "form_type": "base",
         "work": work,
         "agree_to_agreement_error":agree_to_agreement_error,
         }
    return render_to_response("artbase/submit.html", d, context)


@login_required
def edit_artwork_details(request, id):
    context = RequestContext(request)
    agree_to_agreement_error = False
    
    work = can_edit_artwork(request, id)
    if not work:
        return HttpResponseRedirect(reverse(featured))
       
    # NOTE: we use the CouchDB document for the multi-form, NOT the ArtworkStub model
    work_document = work.get_document()

    if request.method == "POST":
        if request.POST["status"] == "delete":
            return HttpResponseRedirect(reverse(delete_artwork, args=[id]))
                
        #due to tag updating requirements, save the multi_form first
        multi_form = ArtworkDetailsForm(request.POST, instance=work_document)
        
        if multi_form.is_valid():
            # instance is a InstanceProxy object

            # IMPORTANT: commit must be false unless you want to trigger many writes
            # to the same Artwork document - David
            #instance = multi_form.save(commit=False)
             
            #shit's messy. needs to be refactored. 
            #right now we have to trigger many writes to keep all together
            instance = multi_form.save()
                  
            #if multi form ok, and user is staff, update the tags
            if request.user.is_staff:
                approve_tags_form = ApproveTagsForm(instance.model, request.POST)
                if approve_tags_form.is_valid():
                    # update the instance with all the stuff going down in the approve tags form
                    # can't save in approve tags form because of couchdb conflict 
                    instance.model, instance.document = approve_tags_form.save(instance.model, commit=False)
            else:
                approve_tags_form = None

            instance = sync_document_and_stub(multi_form_instance_proxy_object = instance)
                        
            if request.POST["status"] == "publish":
                if instance.model.agree_to_agreement:
                    instance.model.submitted_date = datetime.datetime.now()
                    instance.document.submitted_date = datetime.datetime.now()
                    instance.model.status = "awaiting"
                    instance.document.status  = "awaiting"
                    instance.save()
                    return HttpResponseRedirect("%s" % instance.model.view_url())
                else:
                    agree_to_agreement_error = True

            instance.save()

            if request.POST["status"] == "preview":
                return HttpResponseRedirect("/artbase/artwork/%s/preview" % instance.model.id)

            if request.POST["status"] == "view":
                return HttpResponseRedirect("/artbase/artwork/%s/" % instance.model.id)
            
            if request.POST["status"] == "save draft" or request.POST["status"] == "update":
                return HttpResponseRedirect("/artbase/artwork/%s/edit/details/" % instance.model.id)

        else:
            print "-----------------------------------------------------------------------------"
            print "INVALID DETAILS FORM"
            print multi_form.errors
            print "-----------------------------------------------------------------------------"

    else:
        multi_form = ArtworkDetailsForm(instance=work_document)
        
        if request.user.is_staff:
            approve_tags_form = ApproveTagsForm(work)
        else:
            approve_tags_form = None
                  
    tech_categories = Technology.objects.values("category").distinct()
    
    d = {"include_section_header": True,
         "section_title": "Let's say I submit, then what?",
         "multi_form": multi_form,
         "form_path": "artbase/forms/artwork_details.html",
         "form_type": "details",
         "work": work,
         "work_model": work,
         "approve_tags_form":approve_tags_form,
         #"other_artists": work_document.other_artists,
         "agree_to_agreement_error":agree_to_agreement_error,
         "tech_categories": ["%s" % tech["category"] for tech in tech_categories]}
    return render_to_response("artbase/submit.html", d, context)

            
@login_required
def edit_artwork_media(request, id):
    context = RequestContext(request)
    notice = ''
    work = can_edit_artwork(request, id)
    agree_to_agreement_error = False

    if not work:
        return HttpResponseRedirect(reverse(featured))

    if request.GET.get("delete_audio"):
        delete_id = request.GET.get("delete_audio")
        try:
            to_be_deleted = Audio.objects.get(id = delete_id)
            to_be_deleted.delete()
            work_document = work.get_document() 
            for audio in work_document.audio:
                if "%s" % audio.audio_id == "%s" % delete_id:
                    work_document.audio.remove(audio)
            work_document.store(db)
        except Audio.DoesNotExist:
            pass        
        #return HttpResponseRedirect(reverse(edit_artwork_media, args=[id]))
        return HttpResponseRedirect("/artbase/artwork/%s/edit/media" % id)

        
    if request.GET.get('delete_video'):
        delete_id = request.GET.get('delete_video')

        try:
            to_be_deleted = Video.objects.get(id=delete_id)
            to_be_deleted.delete()
            work_document = work.get_document() 

            # iterate over a copy of the list (hence [:])
            for video in work_document.videos[:]:
                if '%s' % video.video_id == '%s' % delete_id:
                    work_document.videos.remove(video)

            work_document.store(db)
        except Video.DoesNotExist:
            pass   

        return HttpResponseRedirect('/artbase/artwork/%s/edit/media' % id)


    if request.method == "POST":
        if request.POST["status"] == "delete":
            #return HttpResponseRedirect(reverse(delete_artwork, args=[id]))
            return HttpResponseRedirect("/artbase/artwork/%s/delete" % id)

        form = ArtworkMediaForm(request.POST, request.FILES or None, instance=work)
        
        if form.is_valid():
        
            #check to make sure file size ok
            total_file_size = 0
            for key, file in request.FILES.items():
                total_file_size = total_file_size + file.size
                
            if total_file_size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
                #return HttpResponseRedirect("%s?exceeded=True" % reverse(edit_artwork_media, args=[instance.id]))
                return HttpResponseRedirect("/artbase/artwork/%s/edit/media?exceeded=True" % work.id)

            else:                        
                instance = form.save()   
                
                if request.POST["status"] == "preview":
                    #return HttpResponseRedirect(reverse(preview_artwork, args=[instance.id]))
                    return HttpResponseRedirect("/artbase/artwork/%s/preview" % instance.id)
                
                if request.POST["status"] == "view":
                    #return HttpResponseRedirect(reverse(preview_artwork, args=[instance.id]))
                    return HttpResponseRedirect("/artbase/artwork/%s/" % instance.id)
                    
                if request.POST["status"] == "publish":
                    if instance.agree_to_agreement:
                        instance.submitted_date = datetime.datetime.now()
                        instance.status = "awaiting"
                        instance.save()
                        return HttpResponseRedirect("%s" % instance.view_url())
                    else:
                        agree_to_agreement_error = True
                
                if request.POST["status"] == "save draft" or request.POST["status"] == "update":
                    #return HttpResponseRedirect(reverse(edit_artwork_media, args=[instance.id]))
                    return HttpResponseRedirect("/artbase/artwork/%s/edit/media" % instance.id)
    else:
        form = ArtworkMediaForm(instance=work)
    
    d = {"include_section_header": True,
         "section_title": "Let's say I submit, then what?",
         "form": form,
         "form_path": "artbase/forms/artwork_media.html",
         "form_type": "media",
         "work": work,
         "notice":notice,
         "agree_to_agreement_error":agree_to_agreement_error}
    return render_to_response("artbase/submit.html", d, context)


@login_required
def edit_artwork_license(request, id):
    context = RequestContext(request)

    work = can_edit_artwork(request, id)
    
    agreement_page_agree_to_agreement_error = False
    
    if not work:
        return HttpResponseRedirect(reverse(featured))

    if request.method == "POST":
        if request.POST["status"] == "delete":
            #return HttpResponseRedirect(reverse(delete_artwork, args=[id]))
            return HttpResponseRedirect("/artbase/artwork/%s/delete" % id)

        form = ArtworkLicenseAgreementForm(request.POST, instance=work)
        
        if form.is_valid():
            #license_slug = form.cleaned_data["license_slug"].replace("cc_", "")
            change_license = request.POST.get("toggle-license-form")

            if change_license:
                use_cc_license = request.POST.get("use_cc_license")
                if use_cc_license == 'No':
                    license = License.objects.get(slug = "arr")
                else:
                    license_slug = request.POST.get("license_select")
                    if license_slug:            
                        license = License.objects.get(slug = license_slug)
                    elif work.license:
                        license = work.license
                    else:
                        license = License.objects.get(slug = "arr")
                
            else:
                license = work.license
            
            instance = form.save(commit=True)
            instance.license = license
            instance.agree_to_agreement = form.cleaned_data["agree_to_agreement"]
            instance.save()
                        
            work_document = instance.get_document() 
            work_document.license = dict(
                title = "%s" % license.title,
                slug = "%s" % license.slug,
                url = "%s" % license.url,
                image = "%s" % license.image,
            )    
                    
            work_document.agree_to_agreement = form.cleaned_data["agree_to_agreement"]
            work_document.store(db)
            
            if request.POST["status"] == "preview":
                #return HttpResponseRedirect(reverse(preview_artwork, args=[instance.id]))
                return HttpResponseRedirect("/artbase/artwork/%s/preview" % instance.id)

            if request.POST["status"] == "view":
                #return HttpResponseRedirect(reverse(preview_artwork, args=[instance.id]))
                return HttpResponseRedirect("/artbase/artwork/%s/" % instance.id)
                
            if request.POST["status"] == "publish":
                if instance.agree_to_agreement:
                    instance.submitted_date = datetime.datetime.now()
                    instance.status = "awaiting"
                    instance.save()
                    return HttpResponseRedirect("%s" % instance.view_url())
                else:
                    agreement_page_agree_to_agreement_error = True
                    form.errors["agree_to_agreement"] = ErrorList([u"You must agree to the agreement before you work can be published."])
            
            if request.POST["status"] == "save draft" or request.POST["status"] == "update":
                #return HttpResponseRedirect(reverse(edit_artwork_license, args=[instance.id]))
                return HttpResponseRedirect("/artbase/artwork/%s/edit/license" % instance.id)
    else:
        form = ArtworkLicenseAgreementForm(instance=work)

    d = {"include_section_header": True,
         "section_title": "Let's say I submit, then what?",
         "form": form,
         "form_path": "artbase/forms/artwork_license_agreement.html",
         "form_type": "license",
         "work": work,
         "agreement_page_agree_to_agreement_error":agreement_page_agree_to_agreement_error,
         "artist_agreement": ArtistAgreement.objects.get(pk=1),
         "licenses": License.objects.exclude(type = "all_rights_reserved"),
         "software_licenses": License.objects.filter(type = "software"),
         "cc_licenses": License.objects.filter(type = "creative_commons"),
         "pd_licenses": License.objects.filter(type = "public_domain"),
         }
    return render_to_response("artbase/submit.html", d, context)


@login_required
def delete_artwork(request, id):
    work = can_edit_artwork(request, id)

    if not work:
        return HttpResponseRedirect(reverse(featured))
        
    if work and request.user == work.user:
        work.remove()
        params = {"flash": "deleted"}
        return HttpResponseRedirect("/profiles/edit/?updated=true")
    else:
        raise Http404


def validate_artwork(work):
    if work.title in [None, ""]:
        return (False, "Please a provide the title of the artwork.")
    if work.summary in [None, ""]:
        return (False, "Please provide a summary of the artwork.")
    if work.description in [None, ""]:
        return (False, "Please provide a description of the artwork.")
    if not work.agree_to_agreement:
        return (False, "Please agree to the Rhizome agreement.")
    if not work.url:
        return (False, "Please specify a url where we can view the artwork.")
    return (True, None)


@login_required
def publish_artwork(request, id):
    context = RequestContext(request)

    work = can_edit_artwork(request, id)

    if request.user != work.user:
        return HttpResponseRedirect(reverse(featured))

    valid, error = validate_artwork(work)
    valid = True
    if valid:
        work.publish_date = datetime.datetime.now()
        work.status = "awaiting"
        work.save()
        return render_to_response("artbase/published.html", context)
    else:
        d = { "error": error }
        return render_to_response("artbase/publish_error.html", d, context)

def get_tech_types(request):
    '''
    AJAX VIEWS FOR DETAILS FORM
    '''
    context = RequestContext(request)
    category = request.GET.get("category")
    if category:
        types = ["%s" % tech["type"] for tech in Technology.objects.values("type").filter(category=category).distinct()]
        if types:
            d = {"types":types}
            return render_to_response("artbase/type_select.html", d, context)
        else:
            raise Http404
    else:
        raise Http404


def get_tech_versions(request):
    '''
    AJAX VIEWS FOR DETAILS FORM
    '''
    context = RequestContext(request)
    type = request.GET.get("type")
    if type:
        versions = ["%s" % tech["version"] for tech in Technology.objects.values("version").filter(type=type)]
        if versions:
            d = {"versions":versions}
            return render_to_response("artbase/version_select.html", d, context)
        else:
            raise Http404
    else:
        raise Http404
        

def tag(request, slug=None):
    """
    List all of the artworks that match a particular tag.
    """
    context = RequestContext(request)
    
    if not slug:
        return HttpResponseRedirect("/artbase/browse/tag")
        
    try:
        atag = Tag.objects.get(slug=slug, type="artbase") #get by slug
    except:
        atag = get_object_or_404(Tag, name=slug, type="artbase") #or try by name
    
    artworks = TaggedItem.objects.get_by_model(ArtworkStub, atag)
    artwork_paginator = RhizomePaginator(artworks, per_page=15, url=(reverse(tag, args=[atag.slug])))
    artwork_paginator.set_current_page(request.GET.get("page"))

    d = {"tag": atag,
         "artwork_paginator": artwork_paginator}
    return render_to_response("artbase/tag.html", d, context)

def member_exhibitions_tag(request, slug=None):
    """
    List all of the exhibitions that match a particular tag.
    """
    context = RequestContext(request)
    
    if not slug:
        return HttpResponseRedirect("/artbase/browse/tag/")

    try:
        atag = Tag.objects.get(slug=slug, type="member_exhibition") #get by slug
    except:
        atag = get_object_or_404(Tag, name=slug, type="member_exhibition") #or try by name
    
    exhibitions = TaggedItem.objects.get_by_model(MemberExhibition, atag)
    exhibitions_paginator = RhizomePaginator(exhibitions, per_page=15, url=(reverse(tag, args=[atag.slug])))
    exhibitions_paginator.set_current_page(request.GET.get("page"))

    d = {"tag": atag,
         "exhibitions_paginator": exhibitions_paginator}
    return render_to_response("artbase/exhibition_tag.html", d, context)

def browse_by_title(request):
    '''
    paginated browsing of artworks by title. 
    ''' 
    context = RequestContext(request)
    sort = request.GET.get("sort")
        
    if sort:
        works = ArtworkStub.objects.filter(status = "approved").filter(title__istartswith=sort).order_by('title').exclude(needs_repair=True)
        browse_paginator = RhizomePaginator(works, per_page=25, url=request.get_full_path())
    else:
        works = ArtworkStub.objects.filter(status = "approved").order_by('title')
        browse_paginator = RhizomePaginator(works, per_page=25, url=request.get_full_path())
    
    alphabet = [chr(i) for i in xrange(ord('a'), ord('z')+1)]
        
    d = {"browse_paginator": browse_paginator,
         "alphabet": alphabet,
         "sort": sort,
         "grouped": browse_helper(request, browse_paginator),
         "browse_type": "title",
         "breadcrumb":(("ArtBase", reverse(featured)),("Browse",None))
    }
    
    return render_to_response("artbase/by_title.html", d, context)


def browse_by_favorites(request):
    '''
    paginated browsing of artworks by number of saves. 
    ''' 
    context = RequestContext(request)
    cursor = connection.cursor()
    cursor.execute("SELECT artworkstub_id, COUNT(id) FROM accounts_rhizomeuser_saved_artworks GROUP BY artworkstub_id HAVING COUNT(id) >= 1 ORDER BY COUNT(id) DESC")
    
    results = []
    for row in cursor:
        id, count = row
        work = ArtworkStub.objects.get(pk=id)
        work.saves = count
        results.append(work)

    d = {
         "grouped": list(split_by(results, 5, pad=True)),
         "browse_type": "favorites",
         "breadcrumb":(("ArtBase", reverse(featured)),("Browse", None))
    }
    
    return render_to_response("artbase/by_favorites.html", d, context)


def browse_by_archived(request):
    '''
    paginated browsing of artworks by archival status. 
    works needing repair are not displayed 
    ''' 
    context = RequestContext(request)
        
    works = ArtworkStub.objects.filter(status = "approved").filter(location_type="cloned").exclude(needs_repair=True).filter(location__contains = "archive.rhizome.org").exclude(created_date=None).order_by('created_date')

    browse_paginator = RhizomePaginator(works, per_page=25, url=request.get_full_path())
    
    alphabet = [chr(i) for i in xrange(ord('a'), ord('z')+1)]
        
    d = {"browse_paginator": browse_paginator,
         "grouped": browse_helper(request, browse_paginator),
         "browse_type": "archived",
         "breadcrumb":(("ArtBase", reverse(featured)),("Browse",None))
    }
    
    return render_to_response("artbase/by_archived.html", d, context)



def browse_by_artist(request):
    '''
    paginated browsing of artworks by tag. slow b/c having to grab works, 
    then make a list of artist from works w/o duplicates
    ''' 
    context = RequestContext(request)
    sort = request.GET.get("sort")

    if sort:
        works_users = ArtworkStub.objects.filter(status = "approved").select_related("user").filter(user__last_name__istartswith=sort).order_by("user__username","user__first_name","user__last_name")
        users_list = []
        works_users_append = users_list.append # make local variable to speed up
        
        for work in works_users:
            try:
                works_users_append(work.user)
            except:
                #add this exception in case user doesn't exist....
                pass
        cleaned_user_list = remove_duplicates_and_preserve_order(users_list)
        browse_paginator = RhizomePaginator(cleaned_user_list, per_page=100, url=request.get_full_path())
    
    else:
        works_users = ArtworkStub.objects.filter(status = "approved").select_related("user").order_by("user__username","user__first_name","user__last_name")
        users_list = []
        works_users_append = users_list.append # make local variable to speed up
        
        for work in works_users:
            try:
                works_users_append(work.user)
            except:
                #add this exception in case user doesn't exist....
                pass
        
        cleaned_user_list = remove_duplicates_and_preserve_order(users_list)
        browse_paginator = RhizomePaginator(cleaned_user_list, per_page=100, url=request.get_full_path())

    alphabet = [chr(i) for i in xrange(ord('a'), ord('z')+1)]
    
    d = {"browse_paginator": browse_paginator,
         "alphabet": alphabet,
         "sort": sort,
         "grouped": browse_helper(request, browse_paginator, per_row=4),
         "browse_type": "artist",
         "breadcrumb":(("ArtBase", reverse(featured)),("Browse",None))}
    
    return render_to_response("artbase/by_artist.html", d, context)


def browse_by_tag(request):
    '''
    paginated browsing of artworks by tags
    '''
    context = RequestContext(request)
    tags = artbase_approved_tags()
    browse_paginator = RhizomePaginator(tags, per_page=200, url=request.get_full_path())
        
    d = {"browse_paginator": browse_paginator,
         "grouped": browse_helper(request, browse_paginator),
         "browse_type": "tag",
         "breadcrumb":(("ArtBase", reverse(featured)),("Browse",None))}
    
    return render_to_response("artbase/by_tag.html", d, context)

'''
COLLECTIONS
'''

def collections_index(request):
    '''
    landing page for collections
    '''
    if request.user.is_staff:
        return HttpResponseRedirect("/artbase/collections/1")
    else:
        return HttpResponseRedirect("/artbase/featured/")
        

def collection_detail(request, collection_id):
    '''
    landing page for collections
    '''

    context = RequestContext(request)

    collection = get_object_or_404(Collection, pk = collection_id)
    artworks = collection.get_artworks()
    featuring = ["%s" % artwork.byline for artwork in artworks]

    column_word_count = 120
    statement_words = [words for words in collection.statement.split()]
    
#    if collection.curator.bio:
#        curator_info =  [words for words in  collection.curator.bio.split()]
#        curator_info.insert(0, (u"<i style='font-size:11px'>"))
#        curator_info.append(u"<i>")
#        for word in curator_info:
#            statement_words.append(word)
    column_count = math.ceil(len(statement_words) / column_word_count)           

    columns = []
    i = 1   
    while i <= column_count:
        column_words = [words for words in statement_words][:column_word_count]
        column_text = u' '.join(column_words)
        columns.append(column_text)
        statement_words = [words for words in statement_words][column_word_count:]
        i+=1
    
    #group them into pages b/c js having trouble with columns only
    merging_list = []
    pages = []
    count = 0
            
    for c in columns:
        merging_list.append(c)
        count+=1
        if (count % 2) == 0:
            merged = [''.join(x) for x in merging_list]
            pages.append(merged)
            merging_list = []
        #if last item and text leftover, add it to a new page
        if c == columns[-1] and len(merging_list) > 0:
            leftover = [c]
            pages.append(leftover)
 
    if collection.curator.bio:
        curator_info =  ["<b>About the Curator</b><hr /><i style='font-size:14px'>%s</i>" % collection.curator.bio]
        pages.append(curator_info)

    d = {
        "collection": collection,
        "breadcrumb":(("ArtBase", reverse(featured)), ("Collections", None)),
        "artworks": artworks,
        "featuring": featuring,
        "pages":pages,
         }
    
    return render_to_response("artbase/collection_detail.html", d, context)

   # else:
    #    return HttpResponseRedirect("/artbase/featured/")

def collection_artwork_fragment(request, work_id):
    '''
    creates popup fragment view for collection
    '''
    context = RequestContext(request)
    artwork = get_object_or_404(ArtworkStub, pk = work_id)
    
    d = {
        "artwork": artwork
         }
    
    return render_to_response("artbase/collection_work_fragment.html", d, context)

    
