from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import DayTour, DayTourAttraction
from .serializer import DayTourSerializer
from common.permissions import DayTourPermission

class DayTourViewSet(ModelViewSet):
    queryset = DayTour.objects.filter(deleted_at__isnull=True)\
        .select_related("region", "created_by")\
        .prefetch_related("tour_attractions__attraction")
    serializer_class = DayTourSerializer
    permission_classes = [IsAuthenticated, DayTourPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["region", "is_active", "created_by"]
    search_fields = ["unique_code","activity_combination","overnight_location","itinerary_text"]

    ordering_fields = ["display_order", "created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

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