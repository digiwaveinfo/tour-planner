from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Attraction
from .serializer import AttractionSerializer
from .filters import AttractionFilter
from rest_framework.decorators import action
from rest_framework.response import Response
import pandas as pd
from apps.geography.models import Region
from rest_framework.parsers import MultiPartParser, FormParser
from common.permissions import *

class AttractionViewSet(ModelViewSet):
    queryset = Attraction.objects.filter(deleted_at__isnull=True)
    serializer_class = AttractionSerializer
    permission_classes = [IsSuperAdminOrAdminWriteElseReadOnly]
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter,]
    parser_classes = [MultiPartParser, FormParser]
    filterset_class = AttractionFilter
    search_fields = ["name","reference_no","key_features_notes"]
    ordering_fields = ["name","display_order","created_at"]
    ordering = ["display_order"]

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

        created = 0
        skipped = 0

        for _, r in df.iterrows():
            region = Region.objects.filter(id=r.get("region")).first()
            if not region:
                skipped += 1
                continue
            if Attraction.objects.filter(reference_no=r.get("reference_no")).exists():
                skipped += 1
                continue
            Attraction.objects.create(
                region=region,
                reference_no=r.get("reference_no"),
                name=r.get("name"),
                latitude=r.get("latitude"),
                longitude=r.get("longitude"),
            )
            created += 1
        return Response({
            "created": created,
            "skipped": skipped
        })