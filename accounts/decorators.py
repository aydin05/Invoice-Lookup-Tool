from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

def carrier_required(function):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_carrier():
            return function(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper

def customer_or_carrier_required(function):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_carrier() or request.user.is_customer()):
            return function(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper


def customer_required(function):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_customer():
            return function(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper