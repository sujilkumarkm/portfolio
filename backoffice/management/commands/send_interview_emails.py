from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from backoffice.models import Notification, MemberPreferences, NotificationDelivery
from backoffice.eventlog import record_event


class Command(BaseCommand):
    help = "Send due application updates and interview reminders."

    def handle(self, *args, **options):

        now = timezone.now()
        due = Notification.objects.filter(cancelled=False, sent_at=None, due_at__lte=now).filter(
            Q(expires_at=None) | Q(expires_at__gt=now)
        )
        record_event(f"Email sender started; {due.count()} due notification(s); backend={settings.EMAIL_BACKEND.rsplit('.', 2)[-2]}", category="email")
        failures = 0
        for notification_id in due.values_list("pk", flat=True):
            try:
                with transaction.atomic():
                    notification = due.select_for_update().filter(pk=notification_id).first()
                    if notification is None:
                        continue
                    recipients = set(MemberPreferences.objects.filter(
                        **{notification.category: True}, user__is_active=True, user__is_staff=True,
                    ).exclude(user__email="").values_list("user__email", flat=True))
                    if settings.ADMIN_NOTIFICATION_EMAIL:
                        recipients.add(settings.ADMIN_NOTIFICATION_EMAIL)
                    if not recipients:
                        record_event(f"Notification #{notification.pk}: no active subscribed recipients with email addresses", category="email", level="WARNING")
                        continue
                    for email in recipients:
                        delivery, _ = NotificationDelivery.objects.get_or_create(notification=notification, email=email)
                        if delivery.sent_at:
                            continue
                        try:
                            if not send_mail(notification.subject, notification.body,
                                             settings.DEFAULT_FROM_EMAIL, [email]):
                                raise RuntimeError("Mail backend did not accept the message")
                        except (OSError, RuntimeError, ValueError) as error:
                            record_event(f"Notification #{notification.pk}, delivery #{delivery.pk}: failed ({type(error).__name__}); queued for retry", category="email", level="ERROR")
                            failures += 1
                            continue
                        record_event(f"Notification #{notification.pk}, delivery #{delivery.pk}: accepted by {settings.EMAIL_BACKEND}; inbox delivery not confirmed", category="email")
                        delivery.sent_at = timezone.now()
                        delivery.save(update_fields=["sent_at"])
                    if any(email not in set(notification.deliveries.filter(sent_at__isnull=False).values_list("email", flat=True)) for email in recipients):
                        continue
                    notification.sent_at = timezone.now()
                    notification.save(update_fields=["sent_at"])
            except (OSError, RuntimeError, ValueError) as error:
                record_event(f"Notification #{notification_id}: processing failed ({type(error).__name__})", category="email", level="ERROR")
                failures += 1
        record_event(f"Email sender finished; {failures} failure(s)", category="email", level="WARNING" if failures else "INFO")
        if failures:
            raise CommandError(f"{failures} email(s) failed and remain queued.")
