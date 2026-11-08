import os

from .settings import *
from .settings import MIDDLEWARE as BASE_MIDDLEWARE

DEBUG = False
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
ALLOWED_HOSTS = ["portfolio.narayam.net"]
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

MIDDLEWARE = [
    BASE_MIDDLEWARE[0],
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *BASE_MIDDLEWARE[1:],
]
WHITENOISE_USE_FINDERS = True
