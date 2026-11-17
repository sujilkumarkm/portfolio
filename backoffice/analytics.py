import re
import secrets

from django.conf import settings
from django.db import DatabaseError
from django.db.models import F
from django.utils import timezone
from .geolocation import public_ip, locate
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
    identifier = identifier or secrets.token_urlsafe(32)
    address = public_ip(request)
    country, region = locate(address)
    if settings.TRUST_GEO_HEADERS:
        candidate = request.headers.get("CF-IPCountry", "").upper()
        if re.fullmatch(r"[A-Z]{2}", candidate) and candidate not in {"XX", "T1"}:
            country = candidate
            region = request.headers.get("CF-Region", "").strip()[:100]

    try:
        visitor, created = Visitor.objects.get_or_create(
            identifier=salted_hmac(COOKIE, identifier, algorithm="sha256").hexdigest(),
            defaults={"country": country, "region": region, "ip_address": address, "last_seen": timezone.now()},
        )
        if not created:
            Visitor.objects.filter(pk=visitor.pk).update(
                ip_address=address, country=country or visitor.country,
                region=region if country else visitor.region,
                last_seen=timezone.now(), visits=F("visits") + 1,
            )
    except DatabaseError:
        return JsonResponse({"enabled": False}, status=503)

    response.set_signed_cookie(
        COOKIE, identifier, salt=COOKIE,
        max_age=MAX_AGE, secure=request.is_secure(), httponly=True, samesite="Lax",
    )
    return response
