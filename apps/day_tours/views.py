from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import DayTour, DayTourAttraction
from .serializer import DayTourSerializer
from common.permissions import DayTourPermission
from common.constant import CurrencyType
from django.db import transaction
from rest_framework.parsers import MultiPartParser, FormParser
from apps.geography.models import Region
import secrets
import pandas as pd
import re
import unicodedata
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

    @action(detail=False, methods=["post"], url_path="bulk-upload",
            parser_classes=[MultiPartParser, FormParser])
    def bulk_upload(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "File required"}, status=400)
        try:
            df = pd.read_excel(file)
        except Exception:
            try:
                file.seek(0)
                df = pd.read_csv(file, encoding="utf-8-sig")
            except Exception:
                return Response({"error": "Invalid file. Upload .xlsx or .csv"}, status=400)

        df.columns = df.columns.str.strip().str.lower()
        if "region" not in df.columns or "activity_combination" not in df.columns:
            return Response({"error": "Missing required columns: region, activity_combination"}, status=400)

        # Drop description/instructions row
        desc_mask = df.apply(
            lambda row: row.astype(str).str.upper().str.startswith(("REQUIRED", "OPTIONAL")).any(), axis=1
        )
        df = df[~desc_mask]

        def _norm(s):
            s = s.strip().lower()
            return unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("ASCII")

        all_regions = Region.objects.all()
        region_map = {_norm(r.name): r for r in all_regions}

        valid_currencies = {c[0] for c in CurrencyType.CHOICES}
        valid_modes = {"OPEN", "DATE_RANGE", "MONTH", "YEAR"}

        records = df.to_dict("records")
        created_count = 0
        skipped = 0
        errors = []

        with transaction.atomic():
            for idx, row in enumerate(records, start=2):
                region_raw = str(row.get("region") or "").strip()
                activity = row.get("activity_combination")

                if not activity or (isinstance(activity, float) and pd.isna(activity)):
                    errors.append(f"Row {idx}: Missing activity_combination — skipped")
                    skipped += 1
                    continue
                activity = str(activity).strip()

                region = region_map.get(_norm(region_raw))
                if not region:
                    errors.append(f"Row {idx}: Region '{region_raw}' not found — skipped")
                    skipped += 1
                    continue

                def _str(v):
                    return str(v).strip() if v is not None and not (isinstance(v, float) and pd.isna(v)) else None
                def _dec(v):
                    try:
                        return float(v) if v is not None and not (isinstance(v, float) and pd.isna(v)) else None
                    except (ValueError, TypeError):
                        return None
                def _int(v, default=0):
                    try:
                        return int(v) if v is not None and not (isinstance(v, float) and pd.isna(v)) else default
                    except (ValueError, TypeError):
                        return default

                validity_mode = (_str(row.get("validity_mode")) or "OPEN").upper()
                if validity_mode not in valid_modes:
                    validity_mode = "OPEN"

                currency = (_str(row.get("currency")) or "INR").upper()
                if currency not in valid_currencies:
                    currency = "INR"

                itinerary_text = _str(row.get("itinerary_text")) or activity

                DayTour.objects.create(
                    region=region,
                    unique_code=self._generate_unique_code(),
                    validity_mode=validity_mode,
                    valid_from=_str(row.get("valid_from")),
                    valid_to=_str(row.get("valid_to")),
                    price=_dec(row.get("price")),
                    currency=currency,
                    activity_combination=activity,
                    itinerary_text=itinerary_text,
                    est_time_distance=_str(row.get("est_time_distance")),
                    overnight_location=_str(row.get("overnight_location")),
                    source_file=_str(row.get("source_file")),
                    display_order=_int(row.get("display_order")),
                    created_by=request.user,
                    is_active=True,
                )
                created_count += 1

        return Response({
            "total_file_records": len(records),
            "created": created_count,
            "skipped": skipped,
            "errors": errors[:20],
        })