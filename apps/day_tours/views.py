from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import DayTour, DayTourAttraction
from .serializer import DayTourSerializer
from common.permissions import DayTourPermission
from django.db import transaction
import secrets
from django.db.models import Q
from common.constant import UserRoletype

class DayTourViewSet(ModelViewSet):
    serializer_class = DayTourSerializer
    permission_classes = [DayTourPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["region", "is_active", "created_by",
    "validity_mode",]
    search_fields = ["unique_code","activity_combination","overnight_location","itinerary_text"]
    ordering_fields = ["display_order", "created_at"]

    def _generate_unique_code(self):
        while True:
            random_number = secrets.randbelow(900000) + 100000
            code = f"DT-{random_number}"
            if not DayTour.objects.filter(unique_code=code).exists():
                return code

    def perform_create(self, serializer):
        with transaction.atomic():
            generated_code = self._generate_unique_code()
            serializer.save(created_by=self.request.user,unique_code=generated_code)

    def get_queryset(self):
        user = self.request.user
        base_queryset = DayTour.objects.filter(
            deleted_at__isnull=True
        ).select_related("region", "created_by")\
         .prefetch_related("tour_attractions__attraction")

        if not user or not user.is_authenticated:
            return base_queryset

        if user.role == UserRoletype.SUPER_ADMIN:
            return base_queryset

        if user.role == UserRoletype.AGENT:
            if user.flag:
                return base_queryset.filter(
                    Q(created_by=user) |
                    Q(created_by__role=UserRoletype.SUPER_ADMIN)
                )
            return base_queryset.filter(created_by=user)

        if user.role == UserRoletype.USER:
            return base_queryset.filter(
                created_by__role=UserRoletype.AGENT
            )
        return base_queryset.none()

    def perform_destroy(self, instance):
        from django.utils import timezone
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=True, methods=["post"])
    def add_attractions(self, request, pk=None):
        tour = self.get_object()
        attractions = request.data.get("attractions", [])
        objs = []
        for item in attractions:
            objs.append(
                DayTourAttraction(
                    day_tour=tour,
                    attraction_id=item["attraction_id"],
                    visit_order=item.get("visit_order", 1)
                )
            )
        DayTourAttraction.objects.bulk_create(objs, ignore_conflicts=True)
        return Response({"message": "Attractions linked successfully"})

    @action(detail=False, methods=["post"])
    def remove_attraction(self, request, pk=None):
        day_tour_id = request.data.get("day_tour_id")
        attraction_id = request.data.get("attraction_id")
        if not day_tour_id or not attraction_id:
            return Response({"error": "day_tour_id and attraction_id required"}, status=400)
        deleted, _ = DayTourAttraction.objects.filter(day_tour_id=day_tour_id,attraction_id=attraction_id).delete()

        return Response({
            "message": "Removed successfully",
            "deleted": deleted
        })