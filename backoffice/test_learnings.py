import json
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from .learnings import learning_progress
from .models import LearningEntry


class LearningTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser('learner')
        self.client.force_login(self.user)
        self.url = reverse('admin:learnings')
        self.today = date(2026, 11, 10)
        self.clock = patch('backoffice.learnings.timezone.localdate', return_value=self.today)
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def post(self, action='draft', ideas=None, day='2026-11-10'):
        return self.client.post(self.url, json.dumps({'date': day, 'action': action, 'ideas': ideas if ideas is not None else [{'heading': 'Transactions', 'explanation': 'Keep changes atomic.'}]}), content_type='application/json')

    def test_draft_and_finalized_content_are_separate(self):
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(learning_progress(self.user)['completed'], 0)
        self.assertEqual(self.post('save').status_code, 200)
        self.post(ideas=[{'heading': 'New draft', 'explanation': ''}])
        entry = LearningEntry.objects.get()
        self.assertEqual(entry.ideas[0]['heading'], 'Transactions')
        self.assertEqual(entry.draft[0]['heading'], 'New draft')
        self.assertEqual(learning_progress(self.user)['percent'], 10)
        response = self.client.get(self.url)
        self.assertContains(response, 'New draft')
        self.assertContains(response, 'Transactions')
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 200)

    def test_rejects_past_future_and_invalid_entries(self):
        for day in ['2026-11-09', '2026-11-11']:
            self.assertEqual(self.post(day=day).status_code, 400)
        for ideas in [[], [{}] * 11, [{'heading': 'Incomplete', 'explanation': ''}]]:
            self.assertEqual(self.post('save', ideas).status_code, 400)
        self.assertFalse(LearningEntry.objects.exists())
        self.assertEqual(self.post('save', [{'heading': 'Idea', 'explanation': 'Details'}] * 10).status_code, 200)
        self.assertEqual(self.post('save').status_code, 200)
        self.assertEqual(LearningEntry.objects.count(), 1)

    def test_private_per_user_and_requires_admin(self):
        self.post('save')
        other = get_user_model().objects.create_user('other', is_staff=True)
        self.client.force_login(other)
        self.assertNotContains(self.client.get(self.url), 'Transactions')
        self.assertEqual(learning_progress(other)['completed'], 0)
        self.assertEqual(Client().get(self.url).status_code, 302)
        ordinary = get_user_model().objects.create_user('ordinary')
        self.client.force_login(ordinary)
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_calendar_progress_and_colors(self):
        for day in range(1, 11):
            LearningEntry.objects.create(user=self.user, date=date(2026, 11, day), saved_at='2026-11-10T12:00:00Z', ideas=[{'heading': 'Idea', 'explanation': 'Details'}])
        progress = learning_progress(self.user)
        self.assertEqual(progress['percent'], 100)
        self.assertEqual(progress['color'], '#16a34a')
        LearningEntry.objects.filter(date__day__gt=5).delete()
        self.assertEqual(learning_progress(self.user)['percent'], 50)
        self.assertEqual(learning_progress(self.user)['color'], '#ea580c')
        self.assertEqual(learning_progress(self.user, date(2024, 2, 1))['elapsed'], 29)
