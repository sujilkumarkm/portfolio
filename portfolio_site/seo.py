from urllib.parse import urlsplit

from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.urls import reverse


SITE_ORIGIN = "https://sujil.net"
CANONICAL_HOST = urlsplit(SITE_ORIGIN).netloc
SITE_NAME = "Sujil Mani"
SHARE_IMAGE = "sujil-mani-preview.jpg"


def canonical_host_redirect(get_response):
    def middleware(request):
        if request.get_host().lower() != CANONICAL_HOST:
            return HttpResponsePermanentRedirect(SITE_ORIGIN + request.get_full_path())
        return get_response(request)

    return middleware


def page_metadata(route, title, description):
    return {
        "site_origin": SITE_ORIGIN,
        "site_name": SITE_NAME,
        "page_url": SITE_ORIGIN + reverse(route),
        "page_title": title,
        "description": description,
        "share_image": SHARE_IMAGE,
    }


def robots_txt(request):
    sitemap_url = SITE_ORIGIN + reverse("sitemap")
    return HttpResponse(
        f"User-agent: *\nAllow: /\n\nSitemap: {sitemap_url}\n",
        content_type="text/plain; charset=utf-8",
    )
