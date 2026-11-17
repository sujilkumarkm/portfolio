from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from backoffice.models import Notification


class Command(BaseCommand):
    help = "Send due application updates and interview reminders."

    def handle(self, *args, **options):
        if not settings.ADMIN_NOTIFICATION_EMAIL:
            raise CommandError("Set ADMIN_NOTIFICATION_EMAIL before running this command.")

        now = timezone.now()
        due = Notification.objects.filter(cancelled=False, sent_at=None, due_at__lte=now).filter(
            Q(expires_at=None) | Q(expires_at__gt=now)
        )
        failures = 0
        for notification_id in due.values_list("pk", flat=True):
            try:
                with transaction.atomic():
                    notification = due.select_for_update().filter(pk=notification_id).first()
                    if notification is None:
                        continue
                    if not send_mail(
                        notification.subject, notification.body, settings.DEFAULT_FROM_EMAIL,
                        [settings.ADMIN_NOTIFICATION_EMAIL],
                    ):
                        raise RuntimeError("Mail backend did not accept the message")
                    notification.sent_at = timezone.now()
                    notification.save(update_fields=["sent_at"])
            except (OSError, RuntimeError, ValueError):
                failures += 1
        if failures:
            raise CommandError(f"{failures} email(s) failed and remain queued.")
