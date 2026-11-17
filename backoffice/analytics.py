import re
import secrets

from django.conf import settings
from django.db import DatabaseError
from django.http import JsonResponse
from django.utils.crypto import salted_hmac
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .models import Visitor

COOKIE = "portfolio_visitor"
MAX_AGE = 365 * 24 * 60 * 60


@never_cache
@require_POST
def analytics(request):
    response = JsonResponse({"enabled": request.POST.get("choice") == "allow"})
    if request.POST.get("choice") != "allow":
        response.delete_cookie(COOKIE, samesite="Lax")
        return response

    identifier = request.get_signed_cookie(COOKIE, default=None, salt=COOKIE, max_age=MAX_AGE)
    if identifier:
        return response

    identifier = secrets.token_urlsafe(32)
    country = ""
    region = ""
    if settings.TRUST_GEO_HEADERS:
        candidate = request.headers.get("CF-IPCountry", "").upper()
        if re.fullmatch(r"[A-Z]{2}", candidate) and candidate not in {"XX", "T1"}:
            country = candidate
            region = request.headers.get("CF-Region", "").strip()[:100]

    try:
        Visitor.objects.create(
            identifier=salted_hmac(COOKIE, identifier, algorithm="sha256").hexdigest(),
            country=country,
            region=region,
        )
    except DatabaseError:
        return JsonResponse({"enabled": False}, status=503)

    response.set_signed_cookie(
        COOKIE, identifier, salt=COOKIE,
        max_age=MAX_AGE, secure=request.is_secure(), httponly=True, samesite="Lax",
    )
    return response
