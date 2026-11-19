import calendar
import json
from datetime import date

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.utils import timezone

from .models import LearningEntry
from .eventlog import record_event


def learning_progress(user, month=None):
    today = timezone.localdate()
    month = month or today.replace(day=1)
    elapsed = today.day if (month.year, month.month) == (today.year, today.month) else calendar.monthrange(month.year, month.month)[1]
    completed = LearningEntry.objects.filter(user=user, date__year=month.year, date__month=month.month, date__lte=today, saved_at__isnull=False).count()
    ratio = min(completed / elapsed, 1)
    color = '#16a34a' if ratio == 1 else '#ca8a04' if ratio >= .75 else '#ea580c' if ratio >= .4 else '#dc2626'
    return {'month': month, 'completed': completed, 'elapsed': elapsed, 'percent': round(ratio * 100), 'degrees': round(ratio * 360), 'color': color}


def learnings(admin_site, request):
    if not request.user.is_active or not request.user.is_staff:
        raise PermissionDenied
    today = timezone.localdate()
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            if not isinstance(payload, dict) or payload.get('date') != today.isoformat():
                return JsonResponse({'error': 'Only today’s learning can be changed. Reload to start a new day.'}, status=400)
            ideas = payload.get('ideas')
            action = payload.get('action')
            if action not in ('draft', 'save') or not isinstance(ideas, list) or not 1 <= len(ideas) <= 10:
                raise ValueError
            cleaned = []
            for idea in ideas:
                if not isinstance(idea, dict) or not isinstance(idea.get('heading'), str) or not isinstance(idea.get('explanation'), str):
                    raise ValueError
                heading, explanation = idea['heading'].strip(), idea['explanation'].strip()
                if len(heading) > 200 or len(explanation) > 20000:
                    raise ValueError
                if action == 'save' and (not heading or not explanation):
                    return JsonResponse({'error': 'Give every idea a heading and explanation before saving.'}, status=400)
                cleaned.append({'heading': heading, 'explanation': explanation})
        except (ValueError, TypeError, UnicodeDecodeError):
            return JsonResponse({'error': 'Use 1–10 ideas, with headings up to 200 characters and explanations up to 20,000 characters.'}, status=400)
        with transaction.atomic():
            entry, _ = LearningEntry.objects.get_or_create(user=request.user, date=today)
            entry = LearningEntry.objects.select_for_update().get(pk=entry.pk)
            if len(entry.ideas) + len(cleaned) > 10:
                return JsonResponse({'error': 'You can save up to 10 ideas per day, including ideas already saved.'}, status=400)
            entry.draft = cleaned
            if action == 'save':
                entry.ideas = entry.ideas + cleaned
                entry.draft = []
                entry.saved_at = timezone.now()
            entry.save()
            record_event("Daily learning saved" if action == "save" else "Learning draft saved", category="learning", actor_id=request.user.pk)
        return JsonResponse({'message': 'Learning saved for today.' if action == 'save' else 'Draft saved', 'saved': action == 'save'})
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        month = date.fromisoformat(request.GET.get('month', today.strftime('%Y-%m')) + '-01')
        if month > today:
            raise ValueError
    except ValueError:
        month = today.replace(day=1)
    entry = LearningEntry.objects.filter(user=request.user, date=today).first()
    history = LearningEntry.objects.filter(user=request.user, date__year=month.year, date__month=month.month, saved_at__isnull=False)
    request.current_app = admin_site.name
    return TemplateResponse(request, 'admin/learnings.html', {
        **admin_site.each_context(request), 'title': 'Learnings', 'today': today,
        'initial_ideas': entry.draft if entry and entry.draft and entry.draft != entry.ideas else [{'heading': '', 'explanation': ''}],
        'remaining_ideas': 10 - len(entry.ideas) if entry else 10,
        'has_draft': bool(entry and entry.draft and entry.draft != entry.ideas),
        'learning': learning_progress(request.user, month), 'history': history,
    })
