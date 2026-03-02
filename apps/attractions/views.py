from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Attraction,AttractionImage
from .serializer import AttractionSerializer,AttractionImageSerializer
from .filters import AttractionFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import FormParser,MultiPartParser
from django.db import transaction
import pandas as pd
from apps.geography.models import Region
from common.permissions import *

class AttractionViewSet(ModelViewSet):
    queryset = Attraction.objects.filter(deleted_at__isnull=True)
    serializer_class = AttractionSerializer
    permission_classes = [DayTourPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    parser_classes = [MultiPartParser, FormParser]
    filterset_class = AttractionFilter
    search_fields = ["name", "reference_no", "key_features_notes"]
    ordering_fields = ["name", "display_order", "created_at"]
    ordering = ["display_order"]

    def create(self, request, *args, **kwargs):
        images = request.FILES.getlist("images")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attraction = serializer.save()

        for img in images:
            AttractionImage.objects.create(
                attraction=attraction,image=img)
        return Response(self.get_serializer(attraction).data)

    @action(detail=False, methods=["post"], url_path="bulk-upload")
    def bulk_upload(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response({"error": "File required"}, status=400)

        try:
            df = pd.read_excel(file, dtype={"reference_no": str})
        except:
            try:
                df = pd.read_csv(file, dtype={"reference_no": str})
            except:
                return Response({"error": "Invalid file"}, status=400)

        df.columns = df.columns.str.strip()

        if "reference_no" not in df.columns:
            return Response({"error": "reference_no column missing"}, status=400)

        df["reference_no"] = (
            df["reference_no"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        required_columns = ["reference_no", "region", "name", "latitude", "longitude"]
        df = df[[col for col in required_columns if col in df.columns]]

        df.dropna(subset=["reference_no"], inplace=True)
        df.drop_duplicates(subset=["reference_no"], inplace=True)

        records = df.to_dict("records")
        region_map = {r.id: r for r in Region.objects.only("id")}
        file_refs = [row["reference_no"] for row in records]

        existing_refs = set(
            Attraction.objects.filter(
                reference_no__in=file_refs
            ).values_list("reference_no", flat=True)
        )

        to_create = []
        skipped = 0

        for row in records:
            ref = row["reference_no"]
            region = region_map.get(row.get("region"))

            if not region:
                skipped += 1
                continue

            if ref in existing_refs:
                skipped += 1
                continue

            to_create.append(
                Attraction(
                    reference_no=ref,
                    region=region,
                    name=row.get("name"),
                    latitude=row.get("latitude"),
                    longitude=row.get("longitude"),
                )
            )

        BATCH_SIZE = 1000

        with transaction.atomic():
            if to_create:
                Attraction.objects.bulk_create(
                    to_create,
                    batch_size=BATCH_SIZE,
                    ignore_conflicts=True  
                )

        return Response({
            "total_file_records": len(records),
            "created": len(to_create),
            "skipped": skipped
        })