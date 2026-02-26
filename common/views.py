from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.account.models import User
from apps.geography.models import Country, Region
from apps.attractions.models import Attraction
from apps.user_plans.models import UserPlan
from apps.day_tours.models import DayTour
from apps.inclusions.models import InclExclCategory, InclusionExclusion
from apps.itinerary_templates.models import ItineraryTemplate, ItineraryTemplateDay, ItineraryTemplateInclExcl
from apps.audit.models import AuditLog

class AdminDashboardViewSet(GenericViewSet):

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def stats(self, request):

        if request.user.role not in ["superadmin", "admin"]:
            return Response({"error": "Permission denied"}, status=403)

        data = {
            "users": User.objects.count(),
            "countries": Country.objects.count(),
            "regions": Region.objects.count(),
            "attractions": Attraction.objects.count(),
            "plans": UserPlan.objects.count(),
            "day_tours": DayTour.objects.count(),
            "inclusions": InclusionExclusion.objects.count(),
            "inclusions_categories": InclExclCategory.objects.count(),
            "itinerary_templates": ItineraryTemplate.objects.count(),
            "itinerary_templates_days": ItineraryTemplateDay.objects.count(),
            "itinerary_templates_incl_excl": ItineraryTemplateInclExcl.objects.count(),

            "recent_users": User.objects.order_by("-id")[:5].values(
                "id","name","email"
            ),

            "recent_logs": AuditLog.objects.order_by("-created_at")[:20].values(
                "action","entity_type","created_at"
            )
        }

        return Response(data)