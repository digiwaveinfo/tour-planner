from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Attraction, AttractionImage
from .serializer import AttractionSerializer
from .filters import AttractionFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser
from django.db import transaction
from django.db.models import Max
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

    def _generate_reference_no(self):
        last = (Attraction.objects.select_for_update().order_by("-id").first())
        if last and last.reference_no:
            try:
                parts = last.reference_no.split("-")
                last_number = int(parts[1])
                next_number = last_number + 1
            except (IndexError, ValueError):
                next_number = Attraction.objects.count() + 1
        else:
            next_number = 1

        return f"ATT-{str(next_number).zfill(4)}"

    def create(self, request, *args, **kwargs):
        images = request.FILES.getlist("images")

        with transaction.atomic():
            generated_ref = self._generate_reference_no()
            data = request.data.copy()
            data["reference_no"] = generated_ref
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            attraction = serializer.save()

            for img in images:
                AttractionImage.objects.create(attraction=attraction,image=img)
        return Response(self.get_serializer(attraction).data)

    @action(detail=False, methods=["post"], url_path="bulk-upload")
    def bulk_upload(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response({"error": "File required"}, status=400)
        try:
            df = pd.read_excel(file)
        except:
            try:
                df = pd.read_csv(file)
            except:
                return Response({"error": "Invalid file"}, status=400)
        df.columns = df.columns.str.strip()
        required_columns = ["region", "name", "latitude", "longitude"]
        df = df[[col for col in required_columns if col in df.columns]]
        records = df.to_dict("records")
        region_map = {r.id: r for r in Region.objects.only("id")}

        created_count = 0
        skipped = 0

        with transaction.atomic():

            last = (Attraction.objects.select_for_update().order_by("-id").first())

            if last and last.reference_no:
                counter = int(last.reference_no.split("-")[1])
            else:
                counter = 0

            to_create = []

            for row in records:
                region = region_map.get(row.get("region"))

                if not region:
                    skipped += 1
                    continue

                counter += 1
                generated_ref = f"ATT-{str(counter).zfill(4)}"

                to_create.append(
                    Attraction(
                        reference_no=generated_ref,
                        region=region,
                        name=row.get("name"),
                        latitude=row.get("latitude"),
                        longitude=row.get("longitude"),
                    )
                )

            if to_create:
                Attraction.objects.bulk_create(to_create, batch_size=1000)
                created_count = len(to_create)

        return Response({
            "total_file_records": len(records),
            "created": created_count,
            "skipped": skipped
        })