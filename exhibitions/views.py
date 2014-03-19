from django.contrib.auth.decorators import user_passes_test
from django.contrib.sites.models import Site
from django.shortcuts import get_object_or_404, render

from exhibitions.models import FrontpageExhibition


@user_passes_test(lambda u: u.is_staff)
def frontpage_exhibition_preview(request, slug):
	exhibition = get_object_or_404(FrontpageExhibition, slug=slug)
	current_site = Site.objects.get_current()
	return render(request, 'exhibitions/frontpage_exhibition.html', {
		'exhibition': exhibition,
		'current_site': current_site,
	})