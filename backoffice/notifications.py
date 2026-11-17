from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import Application, Notification


QUESTIONS = (
    "Why are you interested in this role and this company?",
    "Which past project best demonstrates your fit for this role?",
    "Tell me about a difficult problem you solved and how you measured the outcome.",
    "What would you want to learn about the team and its goals?",
)


def queue_notifications(application, previous):
    now = timezone.now()
    interview = application.interview_at
    body = [
        f"{application.role} at {application.company}",
        f"Stage: {application.get_stage_display()}",
    ]
    if interview:
        body.append(timezone.localtime(interview).strftime("Interview: %A %d %B at %H:%M %Z"))
    for value in (
        application.company_website, application.company_details,
        application.posting_url, application.interview_details,
    ):
        if value:
            body.append(value)
    questions = application.prep_questions.splitlines() or QUESTIONS
    body.extend(["Example interview questions", *(f"- {question}" for question in questions if question.strip())])
    content = "\n\n".join(body)

    if previous is None:
        Notification.objects.create(application=application, category="new_jobs",
            subject=f"New job: {application}", body=content, due_at=now)
    elif any(getattr(previous, field.name) != getattr(application, field.name)
             for field in Application._meta.fields if field.name not in {"id", "updated_at"}):
        Notification.objects.create(
            application=application, subject=f"Application update: {application}",
            body=content,
            due_at=now,
        )

    if previous and any(getattr(previous, field) != getattr(application, field)
                        for field in ("interview_at", "interview_details", "prep_questions")):
        Notification.objects.create(application=application, category="interviews",
            subject=f"Interview update: {application}", body=content, due_at=now)

    pending = Notification.objects.filter(application=application, sent_at=None, expires_at__isnull=False)
    if application.stage in Application.CLOSED or not interview or interview <= now:
        pending.update(cancelled=True)
        return

    if previous and previous.interview_at == interview:
        if pending.filter(cancelled=False).update(body=content):
            return
        if Notification.objects.filter(application=application, expires_at=interview, sent_at__isnull=False).exists():
            return

    pending.update(cancelled=True)
    local_date = timezone.localtime(interview).date()
    reminder = timezone.make_aware(datetime.combine(local_date - timedelta(days=1), time(9)))
    Notification.objects.create(
        application=application, category="interviews", subject=f"Interview reminder: {application}",
        body=content, due_at=max(now, reminder), expires_at=interview,
    )
