import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ["DJANGO_SETTINGS_MODULE"] = "portfolio_site.production"

from portfolio_site.wsgi import application
