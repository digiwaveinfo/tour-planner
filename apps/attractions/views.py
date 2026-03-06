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
import secrets

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
        while True:
            random_number = secrets.randbelow(900000) + 100000
            code = f"ATT-{random_number}"
            if not Attraction.objects.filter(reference_no=code).exists():
                return code

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

    def update(self, request, *args, **kwargs):
        images = request.FILES.getlist("images")
        remove_images = request.data.getlist("remove_images") if hasattr(request.data, 'getlist') else request.data.get("remove_images", [])
        if isinstance(remove_images, str):
            remove_images = [remove_images]

        with transaction.atomic():
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            attraction = serializer.save()

            # Remove images by id
            if remove_images:
                AttractionImage.objects.filter(
                    id__in=[int(i) for i in remove_images],
                    attraction=attraction
                ).delete()

            # Add new images
            for img in images:
                AttractionImage.objects.create(attraction=attraction, image=img)

        return Response(self.get_serializer(attraction).data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(detail=False, methods=["post"], url_path="bulk-upload")
    def bulk_upload(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "File required"}, status=400)
        try:
            df = pd.read_excel(file)
        except Exception:
            try:
                file.seek(0)
                df = pd.read_csv(file)
            except Exception:
                return Response({"error": "Invalid file. Upload .xlsx or .csv"}, status=400)

        df.columns = df.columns.str.strip().str.lower()
        if "name" not in df.columns:
            return Response({"error": "Missing required column: name"}, status=400)

        # Build region lookup maps (by id and by name)
        regions = Region.objects.select_related("country").only("id", "name", "country__name")
        region_id_map = {r.id: r for r in regions}
        region_name_map = {r.name.strip().lower(): r for r in regions}

        records = df.to_dict("records")
        created_count = 0
        skipped = 0
        errors = []
        to_create = []

        with transaction.atomic():
            for idx, row in enumerate(records, start=2):
                # Resolve region by id or name
                region = None
                region_val = row.get("region_id") or row.get("region")
                if region_val is not None:
                    if isinstance(region_val, (int, float)) and not pd.isna(region_val):
                        region = region_id_map.get(int(region_val))
                    elif isinstance(region_val, str) and region_val.strip():
                        region = region_name_map.get(region_val.strip().lower())

                if not region:
                    errors.append(f"Row {idx}: Invalid or missing region '{region_val}'")
                    skipped += 1
                    continue

                name = row.get("name")
                if not name or (isinstance(name, float) and pd.isna(name)):
                    errors.append(f"Row {idx}: Missing name")
                    skipped += 1
                    continue

                lat = row.get("latitude")
                lng = row.get("longitude")
                to_create.append(
                    Attraction(
                        reference_no=self._generate_reference_no(),
                        region=region,
                        name=str(name).strip(),
                        key_features_notes=str(row["key_features_notes"]).strip() if row.get("key_features_notes") and not pd.isna(row.get("key_features_notes")) else None,
                        source_citations=str(row["source_citations"]).strip() if row.get("source_citations") and not pd.isna(row.get("source_citations")) else None,
                        latitude=lat if lat and not pd.isna(lat) else None,
                        longitude=lng if lng and not pd.isna(lng) else None,
                        display_order=int(row["display_order"]) if row.get("display_order") and not pd.isna(row.get("display_order")) else 0,
                    )
                )
            if to_create:
                Attraction.objects.bulk_create(to_create, batch_size=1000)
                created_count = len(to_create)

        return Response({
            "total_file_records": len(records),
            "created": created_count,
            "skipped": skipped,
            "errors": errors[:50],
        })