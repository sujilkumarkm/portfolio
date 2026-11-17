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
        import maxminddb
        with maxminddb.open_database(str(settings.GEOIP_DATABASE_PATH)) as reader:
            result = reader.get(address) or {}
            country = result.get("country", {}).get("iso_code", "")
            subdivisions = result.get("subdivisions", [])
            region = subdivisions[-1].get("names", {}).get("en", "") if subdivisions else ""
            return country, region[:100]
    except Exception:
        logger.warning("IP country lookup unavailable; check the GeoIP database configuration.")
        return "", ""
