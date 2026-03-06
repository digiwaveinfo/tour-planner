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
from django.db.models import Q
from common.constant import UserRoletype
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser
import pandas as pd
from apps.geography.models import Region
from apps.attractions.models import Attraction

class DayTourViewSet(ModelViewSet):
    serializer_class = DayTourSerializer
    permission_classes = [DayTourPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["region", "is_active", "created_by","travel_type",
    "validity_mode",]
    search_fields = ["unique_code","activity_combination","overnight_location","itinerary_text"]
    ordering_fields = ["display_order", "created_at"]
    parser_classes = [MultiPartParser, FormParser,JSONParser]

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

    @action(detail=False, methods=["post"], url_path="bulk-upload")
    def bulk_upload(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "File required"}, status=400)
        try:
            df = pd.read_excel(file)
        except:
            df = pd.read_csv(file)
        created=[]
        skipped=[]
        with transaction.atomic():
            for index,row in df.iterrows():
                region_name=str(row.get("region","")).strip()
                try:
                    region=Region.objects.get(name__iexact=region_name)
                except Region.DoesNotExist:
                    skipped.append({"row":index+1,"reason":"region not found"})
                    continue
                try:
                    valid_from = None if pd.isna(row.get("valid_from")) else row.get    ("valid_from")
                    valid_to = None if pd.isna(row.get("valid_to")) else row.get("valid_to")
                    obj=DayTour.objects.create(
                        region=region,
                        travel_type=row.get("travel_type") or "GENERAL",
                        validity_mode=row.get("validity_mode") or "OPEN",
                        valid_from=valid_from,
                        valid_to=valid_to,
                        price=row.get("price") or 0,
                        currency=row.get("currency") or "EUR",
                        activity_combination=row.get("activity_combination"),
                        est_time_distance=row.get("est_time_distance"),
                        overnight_location=row.get("overnight_location"),
                        source_file=row.get("source_file"),
                        itinerary_text=row.get("itinerary_text"),
                        display_order=row.get("display_order") or 0,
                        created_by=request.user
                    )
                    created.append(obj.unique_code)
                except Exception as e:
                    skipped.append({
                        "row":index+1,
                        "reason":str(e)})
        return Response({
            "created":created,
            "skipped":skipped
        })

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
    
    @action(detail=False, methods=["post"], url_path="bulk-attractions")
    def bulk_attractions(self, request):
        file=request.FILES.get("file")
        df=pd.read_excel(file)
        created=[]
        skipped=[]
        for index,row in df.iterrows():
            try:
                tour=DayTour.objects.get(unique_code=row["day_tour_code"])
                attraction=Attraction.objects.get(reference_no=row["attraction_reference_no"])
                DayTourAttraction.objects.create(
                    day_tour=tour,
                    attraction=attraction,
                    visit_order=row.get("visit_order",1))
                created.append(attraction.reference_no)
            except Exception as e:
                skipped.append({
                    "row":index+1,
                    "reason":str(e)})
        return Response({
            "created":created,
            "skipped":skipped
            })