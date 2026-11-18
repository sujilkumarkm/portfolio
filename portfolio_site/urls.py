from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path, reverse
from django.views.generic.base import RedirectView

from backoffice.admin import site
from backoffice.analytics import analytics

from .seo import SITE_ORIGIN, page_metadata, robots_txt


def home(request):
    metadata = page_metadata(
        "home",
        "Sujil Mani | Support Engineer in Dundalk, Ireland",
        "Sujil Mani (Sujil Kumar), application and IT support engineer in Dundalk, Ireland. "
        "Explore Kaseya experience, web development, data analytics and agentic AI.",
    )
    return render(request, "portfolio.html", metadata)


def software(request):
    return render(
        request,
        "software.html",
        page_metadata(
            "software",
            "Software & Web Developer | Sujil Mani, Ireland",
            "Explore Sujil Mani’s software and web development skills in Dundalk, Ireland: Python, Django, Laravel, Vue.js, SQL and data analytics.",
        ),
    )


def ai(request):
    return render(
        request,
        "ai.html",
        page_metadata(
            "ai",
            "Sujil Mani | Agentic AI & Automation in Ireland",
            "Explore Sujil Mani’s Career Digital Twin, agent engineering capabilities and applied AI workflows.",
        ),
    )


def support(request):
    return render(
        request,
        "support.html",
        page_metadata(
            "support",
            "Application & IT Support Engineer | Sujil Mani, Dundalk",
            "Sujil Mani, support engineer in Dundalk, Ireland, with Kaseya experience in application support, IT troubleshooting, endpoint management and access management.",
        ),
    )


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


def google_site_verification(request):
    return HttpResponse(
        "google-site-verification: google223f70130798bf8b.html",
        content_type="text/html; charset=utf-8",
    )


def sitemap(request):
    page_urls = [SITE_ORIGIN + reverse(route) for route in ("home", "software", "ai", "support", "contact")]
    return render(
        request,
        "sitemap.xml",
        {"page_urls": page_urls},
        content_type="application/xml; charset=utf-8",
    )


urlpatterns = [
    path('admin/', site.urls),
    path('analytics/consent/', analytics, name='visitor_analytics'),
    path("google223f70130798bf8b.html", google_site_verification),
    path("sitemap.xml/google223f70130798bf8b.html", google_site_verification),
    path("robots.txt", robots_txt, name="robots"),
    path("sitemap.xml", sitemap, name="sitemap"),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon-v2.png", permanent=True)),
    path("contact/", contact, name="contact"),
    path("software/", software, name="software"),
    path("ai/", ai, name="ai"),
    path("support/", support, name="support"),
    path("", home, name="home"),
]
