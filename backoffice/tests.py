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
        self.assertContains(response, 'class="dashboard-metrics"')
        self.assertContains(response, 'class="dashboard-locations"')
        self.assertNotContains(response, "dashboard-widgets")
        self.assertNotContains(response, "Move widget")
        self.assertNotContains(response, "Reset widget layout")
        self.assertContains(response, 'aria-label="View all applications"')
        active = self.client.get(response.context["active_url"])
        self.assertEqual(active.status_code, 200)
        self.assertContains(active, self.application.role)
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse("admin:auth_user_changelist")).status_code, 403)


from .models import Visitor
from .geolocation import public_ip
from django.test import RequestFactory

class VisitorAnalyticsTests(TestCase):
    def test_decline_does_not_collect_ip(self):
        self.client.post(reverse("visitor_analytics"), {"choice": "decline"}, REMOTE_ADDR="8.8.8.8")
        self.assertEqual(Visitor.objects.count(), 0)

    @patch("backoffice.analytics.locate", return_value=("GB", "England"))
    def test_consent_tracks_ip_and_repeat_visits(self, locate):
        for _ in range(2):
            self.assertEqual(self.client.post(reverse("visitor_analytics"), {"choice": "allow"}, REMOTE_ADDR="8.8.8.8").status_code, 200)
        visitor = Visitor.objects.get()
        self.assertEqual(visitor.ip_address, "8.8.8.8")
        self.assertEqual(visitor.country, "GB")
        self.assertEqual(visitor.visits, 2)
        self.assertIsNotNone(visitor.last_seen)

    @override_settings(TRUST_GEO_HEADERS=False)
    def test_untrusted_headers_and_private_ip(self):
        request = RequestFactory().get("/", REMOTE_ADDR="8.8.8.8", HTTP_CF_CONNECTING_IP="1.1.1.1")
        self.assertEqual(public_ip(request), "8.8.8.8")
        request.META["REMOTE_ADDR"] = "127.0.0.1"
        self.assertIsNone(public_ip(request))

    @override_settings(TRUST_GEO_HEADERS=True)
    def test_trusted_proxy(self):
        request = RequestFactory().get("/", REMOTE_ADDR="127.0.0.1", HTTP_CF_CONNECTING_IP="1.1.1.1")
        self.assertEqual(public_ip(request), "1.1.1.1")

    def test_map_counts_and_permissions(self):
        for i in range(5): Visitor.objects.create(identifier=str(i), country="GB")
        owner = get_user_model().objects.create_superuser("map-owner", "owner@example.com", "password")
        self.client.force_login(owner)
        response = self.client.get(reverse("admin:visitor_map_data"))
        self.assertEqual(response.json()["countries"], [{"country": "GB", "visitors": 5, "visits": 5}])
        self.assertNotIn("ip_address", response.content.decode())
        self.assertContains(self.client.get(reverse("admin:visitor_map")), 'id="world-map"')
        staff = get_user_model().objects.create_user("map-staff", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("admin:visitor_map_data")).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:visitor_map")).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("admin:visitor_map_data")).status_code, 302)
