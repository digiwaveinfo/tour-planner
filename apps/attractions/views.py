from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Attraction, AttractionImage
from .serializer import AttractionSerializer
from .filters import AttractionFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser,JSONParser
from django.db import transaction
import pandas as pd
from apps.geography.models import Region
from common.permissions import *

class AttractionViewSet(ModelViewSet):
    queryset = Attraction.objects.filter(deleted_at__isnull=True)
    serializer_class = AttractionSerializer
    permission_classes = [DayTourPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    parser_classes = [MultiPartParser, FormParser,JSONParser]
    filterset_class = AttractionFilter
    search_fields = ["name", "reference_no", "key_features_notes"]
    ordering_fields = ["name", "display_order", "created_at"]
    ordering = ["display_order"]

    def create(self, request, *args, **kwargs):
        images = request.FILES.getlist("images")
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
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

            if remove_images:
                AttractionImage.objects.filter(
                    id__in=[int(i) for i in remove_images],
                    attraction=attraction
                ).delete()

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
            df = pd.read_csv(file)
        df.columns = df.columns.str.strip()
        created = []
        skipped = []
        with transaction.atomic():
            for index, row in df.iterrows():
                region_name = str(row.get("region", "")).strip()
                name = str(row.get("name", "")).strip()
                key_features_notes = str(row.get("key_features_notes", "")).strip()
                source_citations = str(row.get("source_citations", "")).strip()
                latitude = row.get("latitude")
                longitude = row.get("longitude")
                display_order = row.get("display_order") or 0
                if not region_name or not name:
                    skipped.append({
                        "row": index + 2,
                        "reason": "Region or Name missing"
                    })
                    continue
                try:
                    region = Region.objects.get(name__iexact=region_name)
                except Region.DoesNotExist:
                    skipped.append({
                        "row": index + 2,
                        "reason": f"Region not found: {region_name}"
                    })
                    continue
                if Attraction.objects.filter(
                    name__iexact=name,
                    region=region
                ).exists():
                    skipped.append({
                        "row": index + 2,
                        "reason": "Duplicate attraction"
                    })
                    continue
                attraction = Attraction.objects.create(
                    region=region,
                    name=name,
                    key_features_notes=key_features_notes,
                    source_citations=source_citations,
                    latitude=latitude,
                    longitude=longitude,
                    display_order=display_order
                )
                created.append({
                    "row": index + 2,
                    "name": attraction.name,
                    "reference_no": attraction.reference_no
                })
        return Response({
            "created_count": len(created),
            "skipped_count": len(skipped),
            "created": created,
            "skipped": skipped
        })