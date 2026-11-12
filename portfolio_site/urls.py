from django.shortcuts import render
from django.urls import path, reverse
from django.views.generic.base import RedirectView

from .seo import SITE_ORIGIN, page_metadata, robots_txt


def home(request):
    metadata = page_metadata(
        "home",
        "Sujil Mani | Application Support, Python & Agentic AI",
        "Explore Sujil Mani's portfolio in Dundalk, Ireland, including application "
        "support experience, Python and Django projects, and agentic AI research.",
    )
    return render(request, "portfolio.html", metadata)


def contact(request):
    return render(
        request,
        "contact.html",
        {
            **page_metadata(
                "contact",
                "Contact Sujil Mani | Dundalk, Ireland",
                "Get in touch with Sujil Mani in Dundalk, County Louth, Ireland, "
                "about application support, Python development or agentic AI projects.",
            ),
            "street_address": "16 Dunlong Avenue",
            "locality": "Avenue Road, Dundalk",
            "region": "County Louth, Ireland",
            "phone": "+353892738178",
        },
    )


def sitemap(request):
    page_urls = [SITE_ORIGIN + reverse(route) for route in ("home", "contact")]
    return render(
        request,
        "sitemap.xml",
        {"page_urls": page_urls},
        content_type="application/xml; charset=utf-8",
    )


urlpatterns = [
    path("robots.txt", robots_txt, name="robots"),
    path("sitemap.xml", sitemap, name="sitemap"),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon-v2.png", permanent=True)),
    path("contact/", contact, name="contact"),
    path("", home, name="home"),
]
