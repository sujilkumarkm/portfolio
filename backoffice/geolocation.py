import ipaddress
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def public_ip(request):
    # Only trust Cloudflare when the origin is restricted to the trusted edge.
    value = request.headers.get("CF-Connecting-IP", "") if settings.TRUST_GEO_HEADERS else request.META.get("REMOTE_ADDR", "")
    try:
        address = ipaddress.ip_address(value)
        return str(address) if address.is_global else None
    except ValueError:
        return None


def locate(address):
    if not address or not settings.GEOIP_DATABASE_PATH:
        return "", ""
    try:
        import geoip2.database
        with geoip2.database.Reader(settings.GEOIP_DATABASE_PATH) as reader:
            if reader.metadata().database_type.endswith("City"):
                result = reader.city(address)
                return result.country.iso_code or "", result.subdivisions.most_specific.name or ""
            return reader.country(address).country.iso_code or "", ""
    except Exception:
        logger.warning("IP country lookup unavailable; check the GeoIP database configuration.")
        return "", ""
