from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from backoffice.geolocation import locate
from backoffice.models import Visitor


class Command(BaseCommand):
    help = "Resolve saved visitor IPs with missing countries using the local database."

    def handle(self, *args, **options):
        if not settings.GEOIP_DATABASE_PATH or not Path(settings.GEOIP_DATABASE_PATH).is_file():
            raise CommandError("Country database missing. Run python manage.py update_geoip first.")
        if not locate("8.8.8.8")[0]:
            raise CommandError("Country database could not be read. Check the database and maxminddb installation.")
        updated = 0
        unresolved = 0
        for visitor in Visitor.objects.filter(country="", ip_address__isnull=False).iterator():
            country, region = locate(visitor.ip_address)
            if country:
                updated += Visitor.objects.filter(pk=visitor.pk, country="", ip_address=visitor.ip_address).update(country=country, region=region)
            else:
                unresolved += 1
        self.stdout.write(f"Updated {updated} visitor(s); {unresolved} unresolved.")
