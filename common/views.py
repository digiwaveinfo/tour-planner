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
from common.constant import UserRoletype

class AdminDashboardViewSet(GenericViewSet):

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def stats(self, request):
        user = request.user
        if not user.is_superuser and user.role != UserRoletype.SUPER_ADMIN:
            return Response({"error": "Permission denied"}, status=403)

        visible_users = User.objects.filter(
            deleted_at__isnull=True, is_superuser=False
        ).exclude(role=UserRoletype.SUPER_ADMIN).exclude(id=user.id)

        data = {
            "user_count": visible_users.count(),
            "country_count": Country.objects.count(),
            "region_count": Region.objects.count(),
            "attraction_count": Attraction.objects.count(),
            "plan_count": UserPlan.objects.count(),
            "day_tour_count": DayTour.objects.count(),
            "inclusion_count": InclusionExclusion.objects.count(),
            "template_count": ItineraryTemplate.objects.count(),

            "recent_users": list(
                visible_users.order_by("-created_at")[:5].values(
                    "id", "name", "email", "role", "created_at"
                )
            ),

            "recent_audit_logs": list(
                AuditLog.objects.order_by("-created_at")[:20].values(
                    "id", "action", "entity_type", "created_at"
                )
            ),
        }

        return Response(data)