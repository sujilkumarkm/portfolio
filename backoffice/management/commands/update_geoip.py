import gzip
import shutil
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = "Install the current DB-IP Country Lite database (CC BY 4.0)."

    def handle(self, *args, **options):
        import maxminddb
        destination = Path(settings.GEOIP_DATABASE_PATH)
        destination.parent.mkdir(parents=True, exist_ok=True)
        month = timezone.now().strftime("%Y-%m")
        url = f"https://download.db-ip.com/free/dbip-country-lite-{month}.mmdb.gz"
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".mmdb", delete=False) as output:
                temporary = Path(output.name)
                with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0 PortfolioGeoIP/1.0"}), timeout=45) as response, gzip.GzipFile(fileobj=response) as source:
                    shutil.copyfileobj(source, output)
            with maxminddb.open_database(str(temporary)) as reader:
                if not reader.get("8.8.8.8"):
                    raise ValueError("Database validation failed")
            temporary.replace(destination)
        except Exception as error:
            raise CommandError(f"Country database update failed ({type(error).__name__}); existing database preserved.") from None
        finally:
            if temporary and temporary.exists():
                temporary.unlink()
        self.stdout.write(self.style.SUCCESS(f"Country database installed: {destination}. IP Geolocation by DB-IP (https://db-ip.com)."))
