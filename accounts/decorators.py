try:
    from functools import update_wrapper, wraps
except ImportError:
    from django.utils.functional import update_wrapper, wraps  # Python 2.4 fallback.
    
from django.contrib.auth import REDIRECT_FIELD_NAME
#from django.contrib.auth.decorators import user_passes_test

from django.http import HttpResponseRedirect
from django.utils.decorators import available_attrs
from django.utils.http import urlquote


def user_passes_membership_test(test_func, membershp_url="/membership_required/", redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)                
            path = urlquote(request.get_full_path())
            return HttpResponseRedirect('%s' % membershp_url)
        return wraps(view_func, assigned=available_attrs(view_func))(_wrapped_view)
    return decorator

def membership_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_membership_test(
        lambda u: u.get_profile().is_member(),
        redirect_field_name=redirect_field_name
    )
    
    if function:
        return actual_decorator(function)
    return actual_decorator