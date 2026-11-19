from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.utils import timezone
from .models import AppEvent


def logs(admin_site, request, data=False):
    if not request.user.is_active or not request.user.is_superuser:
        raise PermissionDenied
    if not data:
        request.current_app = admin_site.name
        return TemplateResponse(request, 'admin/logs.html', {**admin_site.each_context(request), 'title': 'Logs'})
    events = AppEvent.objects.all()
    if request.GET.get('level') in ('INFO', 'WARNING', 'ERROR', 'CRITICAL'):
        events = events.filter(level=request.GET['level'])
    if request.GET.get('category') in ('activity', 'authentication', 'email', 'learning', 'errors'):
        events = events.filter(category=request.GET['category'])
    query = request.GET.get('q', '')[:100]
    if query:
        events = events.filter(message__icontains=query)
    rows = list(events[:500])
    return JsonResponse({'lines': [f'{timezone.localtime(row.created_at):%Y-%m-%d %H:%M:%S %Z} [{row.level}] [{row.category}] user={row.actor_id or "system"} {row.message}' for row in reversed(rows)]})
