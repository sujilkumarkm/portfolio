from django.shortcuts import render
from django.urls import path


def home(request):
    return render(request, "portfolio.html")


def contact(request):
    return render(
        request,
        "contact.html",
        {
            "street_address": "16 Dunlong Avenue",
            "locality": "Avenue Road, Dundalk",
            "region": "County Louth, Ireland",
            "phone": "+353892738178",
        },
    )


urlpatterns = [
    path("contact/", contact, name="contact"),
    path("", home, name="home"),
]
