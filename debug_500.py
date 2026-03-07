import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tourandtravels.settings')
django.setup()

from rest_framework.test import force_authenticate, APIRequestFactory
from apps.user_plans.views import UserPlanViewSet
from apps.account.models import User
from apps.geography.models import Country, Region

user = User.objects.first()

c, _ = Country.objects.get_or_create(id=7, defaults={"name": "Test Country 7"})
r1, _ = Region.objects.get_or_create(id=52, defaults={"name": "Region 52", "country": c})
r2, _ = Region.objects.get_or_create(id=53, defaults={"name": "Region 53", "country": c})

factory = APIRequestFactory()
request = factory.post(
    '/api/v1/user-plans/plans/auto_generate_draft/',
    {
        "country": 7,
        "total_days": 3,
        "start_date": None,
        "travel_type": "GROUP",
        "city_allocations": [
            {"region": 52, "days": 1},
            {"region": 53, "days": 2}
        ]
    },
    format='json'
)
force_authenticate(request, user=user)

view = UserPlanViewSet.as_view({'post': 'auto_generate_draft'})
try:
    response = view(request)
    print("STATUS CODE:", response.status_code)
    try:
        print("RESPONSE:", response.content.decode('utf-8'))
    except:
        pass
except Exception as e:
    import traceback
    traceback.print_exc()
