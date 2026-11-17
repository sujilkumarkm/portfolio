import os

from django.core.exceptions import ImproperlyConfigured

from .settings import *
from .settings import MIDDLEWARE as BASE_MIDDLEWARE, mysql_database

DEBUG = False
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
if not os.getenv("PORTFOLIO_DB_PASSWORD"):
    raise ImproperlyConfigured("Set PORTFOLIO_DB_PASSWORD for the production MySQL account.")
DATABASES = {
    "default": mysql_database(
        os.getenv("PORTFOLIO_DB_USER") or "suji1991_portfolio",
        default_host="localhost",
    ),
}

ALLOWED_HOSTS = ["portfolio.narayam.net", "sujil.net", "www.sujil.net"]
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

MIDDLEWARE = [
    "portfolio_site.seo.canonical_host_redirect",
    BASE_MIDDLEWARE[0],
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *BASE_MIDDLEWARE[1:],
]
WHITENOISE_USE_FINDERS = True
