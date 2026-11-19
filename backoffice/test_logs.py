import logging
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from .models import AppEvent, Application, MemberPreferences
from .notifications import queue_notifications


class LogTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_superuser('log-owner', email='owner@example.com')
        self.client.force_login(self.owner)

    def test_logs_are_superuser_only_and_filterable(self):
        AppEvent.objects.create(category='email', message='Queued notification')
        response = self.client.get(reverse('admin:logs_data'), {'category': 'email'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['lines']), 1)
        self.assertIn('Queued notification', response.json()['lines'][0])
        self.assertContains(self.client.get(reverse('admin:logs')), 'logs-output')
        staff = get_user_model().objects.create_user('staff', is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse('admin:logs')).status_code, 403)
        self.assertEqual(self.client.get(reverse('admin:logs_data')).status_code, 403)

    def test_admin_activity_omits_form_content(self):
        self.client.post(reverse('admin:learnings'), data={'password': 'secret-sentinel'})
        self.assertTrue(AppEvent.objects.filter(message__contains='admin:learnings').exists())
        self.assertFalse(AppEvent.objects.filter(message__contains='secret-sentinel').exists())

    def test_error_metadata_does_not_store_exception_secrets(self):
        try:
            raise ValueError('secret-sentinel')
        except ValueError:
            logging.getLogger('portfolio.test').exception('secret-sentinel')
        event = AppEvent.objects.filter(category='errors').latest('pk')
        self.assertIn('ValueError', event.message)
        self.assertNotIn('secret-sentinel', event.message)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', ADMIN_NOTIFICATION_EMAIL='')
    def test_new_jobs_and_application_updates_send_and_log(self):
        MemberPreferences.objects.create(user=self.owner, new_jobs=True, application_updates=True)
        application = Application.objects.create(role='Engineer', company='Example')
        queue_notifications(application, None)
        self.assertTrue(AppEvent.objects.filter(category='email', message__contains='New-job email queued').exists())
        call_command('send_interview_emails')
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(AppEvent.objects.filter(category='email', message__contains='accepted by').exists())
        previous = Application.objects.get(pk=application.pk)
        application.stage = Application.Stage.SCREENING
        application.save()
        queue_notifications(application, previous)
        call_command('send_interview_emails')
        self.assertEqual(len(mail.outbox), 2)
        self.assertTrue(AppEvent.objects.filter(message__contains='Application-update email queued').exists())
