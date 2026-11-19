from django.apps import AppConfig


class BackofficeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backoffice'

    def ready(self):
        from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
        from .eventlog import record_event
        from django.contrib.admin.models import LogEntry
        from django.db.models.signals import post_save

        def signed_in(sender, request, user, **kwargs):
            record_event('Admin sign-in succeeded', category='authentication', actor_id=user.pk)

        def signed_out(sender, request, user, **kwargs):
            record_event('Admin signed out', category='authentication', actor_id=user.pk if user else None)

        def failed(sender, credentials, request, **kwargs):
            record_event('Sign-in failed', category='authentication', level='WARNING')

        user_logged_in.connect(signed_in, weak=False, dispatch_uid='event_login')
        user_logged_out.connect(signed_out, weak=False, dispatch_uid='event_logout')
        user_login_failed.connect(failed, weak=False, dispatch_uid='event_login_failed')

        def admin_change(sender, instance, created, **kwargs):
            if created:
                action = {1: 'Created', 2: 'Changed', 3: 'Deleted'}.get(instance.action_flag, 'Updated')
                model = instance.content_type.model if instance.content_type else 'object'
                record_event(f'{action} {model} #{instance.object_id}', actor_id=instance.user_id)

        post_save.connect(admin_change, sender=LogEntry, weak=False, dispatch_uid='event_admin_change')
