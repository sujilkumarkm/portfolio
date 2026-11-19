"""Structured operational events. Never pass request bodies or credentials here."""
import logging
from django.db import DatabaseError


def record_event(message, category='activity', level='INFO', actor_id=None):
    from .models import AppEvent
    try:
        AppEvent.objects.create(message=message[:1000], category=category, level=level, actor_id=actor_id)
    except DatabaseError:
        # Logging must not break requests, including before the migration is applied.
        pass


class DatabaseEventHandler(logging.Handler):
    def emit(self, record):
        # Exception messages can contain credentials, SQL values or submitted text.
        # Store safe exception type/location metadata instead of raw messages.
        error_type = record.exc_info[0].__name__ if record.exc_info else 'Error'
        location = ''
        if record.exc_info and record.exc_info[2]:
            tb = record.exc_info[2]
            while tb.tb_next:
                tb = tb.tb_next
            location = f' in {tb.tb_frame.f_code.co_name} at line {tb.tb_lineno}'
        record_event(f'{record.name}: {error_type}{location}', category='errors', level=record.levelname)


class ActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Omit static assets, query strings, request bodies and log refresh traffic.
        if request.path.startswith('/admin/') and not request.path.startswith('/admin/logs/'):
            user = getattr(request, 'user', None)
            actor = user.pk if user and user.is_authenticated else None
            level = 'ERROR' if response.status_code >= 500 else 'WARNING' if response.status_code >= 400 else 'INFO'
            route = getattr(getattr(request, 'resolver_match', None), 'url_name', None) or 'unknown'
            record_event(f'{request.method} admin:{route} — HTTP {response.status_code}', category='activity', level=level, actor_id=actor)
        return response
