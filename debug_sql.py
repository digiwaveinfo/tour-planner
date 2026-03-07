import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tourandtravels.settings')
django.setup()

from apps.day_tours.models import DayTour
from apps.itinerary_templates.models import ItineraryTemplateDay

import logging
l = logging.getLogger('django.db.backends')
l.setLevel(logging.DEBUG)
l.addHandler(logging.StreamHandler())

try:
    print(DayTour.objects.all().query)
    list(DayTour.objects.all()[:1])
except Exception as e:
    print(e)
