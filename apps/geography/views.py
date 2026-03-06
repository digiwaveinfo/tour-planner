from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .models import Country,Region
from .serializer import CountrySerializer,RegionSerializer
from common.permissions import *
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser
from rest_framework import status
import pandas as pd
from django.db import transaction

class CountryViewSet(ModelViewSet):
    queryset = Country.objects.filter(deleted_at__isnull=True)
    serializer_class = CountrySerializer
    permission_classes = [IsSuperAdminOrAdminWriteElseReadOnly]
    parser_classes = [MultiPartParser, FormParser,JSONParser]

    @action(detail=False, methods=["post"], url_path="bulk-upload")
    def bulk_upload(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "File required"}, status=400)
        try:
            df = pd.read_excel(file)
        except:
            df = pd.read_csv(file)
        created = []
        skipped = []
        with transaction.atomic():
            for index, row in df.iterrows():
                name = str(row.get("name", "")).strip()
                code = str(row.get("code", "")).strip()
                iso_code = str(row.get("iso_code", "")).strip()
                if not name or not code:
                    skipped.append({"row": index+1, "reason": "name/code missing"})
                    continue
                exists = Country.objects.filter(name__iexact=name).exists()
                if exists:
                    skipped.append({"row": index+1, "name": name, "reason": "duplicate"})
                    continue
                country = Country.objects.create(name=name,code=code.upper(),iso_code=iso_code.upper() if iso_code else None)
                created.append(country.name)
        return Response({
            "created_count": len(created),
            "skipped_count": len(skipped),
            "created": created,
            "skipped": skipped
        }, status=status.HTTP_201_CREATED)
    
class RegionViewSet(ModelViewSet):
    serializer_class = RegionSerializer
    permission_classes = [IsSuperAdminOrAdminWriteElseReadOnly]
    parser_classes = [MultiPartParser, FormParser,JSONParser]

    def get_queryset(self):
        qs = Region.objects.select_related("country")
        country_id = self.request.query_params.get("country")
        if country_id:
            qs = qs.filter(country_id=country_id)
        return qs

    @action(detail=True, methods=["get"])
    def regions(self, request, pk=None):
        regions = Region.objects.filter(country_id=pk)
        serializer = RegionSerializer(regions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["post"], url_path="bulk-upload")
    def bulk_upload(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "File required"}, status=400)
        try:
            df = pd.read_excel(file)
        except:
            df = pd.read_csv(file)
        created = []
        skipped = []
        with transaction.atomic():
            for index, row in df.iterrows():
                country_code = str(row.get("country_code", "")).strip().upper()
                name = str(row.get("name", "")).strip()
                code = str(row.get("code", "")).strip().upper()
                description = str(row.get("description", "")).strip()
                display_order = row.get("display_order") or 0

                if not country_code or not name or not code:
                    skipped.append({
                        "row": index + 1,
                        "reason": "Missing required fields"
                    })
                    continue
                try:
                    country = Country.objects.get(code__iexact=country_code)
                except Country.DoesNotExist:
                    skipped.append({
                        "row": index + 1,
                        "reason": f"Country not found: {country_code}"
                    })
                    continue
                if Region.objects.filter(code__iexact=code).exists():
                    skipped.append({
                        "row": index + 1,
                        "reason": f"Duplicate region code: {code}"
                    })
                    continue
                region = Region.objects.create(
                    country=country,
                    name=name,
                    code=code,
                    description=description,
                    display_order=display_order
                )
                created.append(region.name)
        return Response({
            "created_count": len(created),
            "skipped_count": len(skipped),
            "created": created,
            "skipped": skipped
        }, status=status.HTTP_201_CREATED)
