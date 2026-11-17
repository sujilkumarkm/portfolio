from io import StringIO
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .models import Application, MemberPreferences, Notification
from .notifications import queue_notifications

@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", ADMIN_NOTIFICATION_EMAIL="")
class NotificationTests(TestCase):
    def setUp(self):
        self.member = get_user_model().objects.create_user("member", email="member@example.com", is_staff=True)
        MemberPreferences.objects.create(user=self.member, new_jobs=True)
        self.application = Application.objects.create(role="Engineer", company="Example")

    def test_new_job_and_preferences(self):
        queue_notifications(self.application, None)
        call_command("send_interview_emails")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.member.email])
        call_command("send_interview_emails")
        self.assertEqual(len(mail.outbox), 1)

    def test_partial_failure_retries_only_failed_recipient(self):
        other = get_user_model().objects.create_user("other", email="other@example.com", is_staff=True)
        MemberPreferences.objects.create(user=other, new_jobs=True)
        queue_notifications(self.application, None)
        def send(subject, body, sender, recipients):
            if recipients == [other.email]: raise OSError("SMTP unavailable")
            return 1
        with patch("backoffice.management.commands.send_interview_emails.send_mail", side_effect=send):
            with self.assertRaises(CommandError): call_command("send_interview_emails")
        call_command("send_interview_emails")
        self.assertEqual([m.to for m in mail.outbox], [[other.email]])

    def test_unsubscribed_and_inactive_members(self):
        self.member.is_active = False
        self.member.save()
        queue_notifications(self.application, None)
        call_command("send_interview_emails")
        self.assertEqual(len(mail.outbox), 0)

    def test_update_categories(self):
        previous = Application.objects.get(pk=self.application.pk)
        self.application.stage = Application.Stage.FIRST
        self.application.interview_details = "Video call"
        queue_notifications(self.application, previous)
        self.assertEqual(set(Notification.objects.values_list("category", flat=True)), {"application_updates", "interviews"})

    def test_dashboard_links_and_member_access(self):
        admin = get_user_model().objects.create_superuser("owner", "owner@example.com", "password")
        self.client.force_login(admin)
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, reverse("admin:backoffice_visitor_changelist"))
        self.assertContains(response, "stage__in=")
        self.assertContains(response, "data-widget=")
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse("admin:auth_user_changelist")).status_code, 403)
