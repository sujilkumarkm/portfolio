from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Send a test message through the configured SMTP service."

    def add_arguments(self, parser):
        parser.add_argument("recipient")

    def handle(self, *args, **options):
        if settings.EMAIL_BACKEND != "django.core.mail.backends.smtp.EmailBackend":
            raise CommandError("Configure the SMTP email backend first; console mail does not verify delivery.")
        try:
            accepted = send_mail("Portfolio email delivery test",
                "This is a test of portfolio dashboard email notifications.",
                settings.DEFAULT_FROM_EMAIL, [options["recipient"]])
        except Exception as error:
            raise CommandError(f"SMTP test failed ({type(error).__name__}). Check the server configuration.") from None
        if accepted != 1:
            raise CommandError("SMTP server did not accept the test message.")
        self.stdout.write(self.style.SUCCESS("SMTP accepted the message. Confirm receipt in the recipient inbox."))
