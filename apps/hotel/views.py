from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Hotel,HotelImage
from .serializer import HotelSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import *
from rest_framework.parsers import MultiPartParser, FormParser
import pandas as pd
from django.db import transaction
from apps.geography.models import Country,Region

class HotelViewSet(ModelViewSet):
    queryset = Hotel.objects.filter(deleted_at__isnull=True)
    serializer_class = HotelSerializer
    permission_classes = [DayTourPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["country", "region", "star_rating", "is_active"]
    search_fields = ["name", "city"]
    ordering_fields = ["name", "city", "created_at"]
    ordering = ["name"]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        images = request.FILES.getlist("images")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        hotel = serializer.save()

        for img in images:
            HotelImage.objects.create(
                hotel=hotel,
                image=img
            )

        return Response(self.get_serializer(hotel).data)
    
    @action(detail=False, methods=["post"], url_path="bulk-upload")
    def bulk_upload(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "File required"}, status=400)
        try:
            df = pd.read_excel(file)
        except:
            df = pd.read_csv(file)
        df.columns = df.columns.str.strip()
        created = []
        skipped = []
        with transaction.atomic():
            for index, row in df.iterrows():
                country_code = str(row.get("country_code", "")).strip().upper()
                region_name = str(row.get("region", "")).strip()
                name = str(row.get("name", "")).strip()
                if not country_code or not region_name or not name:
                    skipped.append({
                        "row": index + 2,
                        "reason": "Missing required fields"
                    })
                    continue
                try:
                    country = Country.objects.get(code__iexact=country_code)
                except Country.DoesNotExist:
                    skipped.append({
                        "row": index + 2,
                        "reason": f"Country not found: {country_code}"
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
                if Hotel.objects.filter(name__iexact=name, region=region).exists():
                    skipped.append({
                        "row": index + 2,
                        "reason": "Duplicate hotel"
                    })
                    continue
                hotel = Hotel.objects.create(
                    country=country,
                    region=region,
                    name=name,
                    city=row.get("city"),
                    address=row.get("address"),
                    star_rating=row.get("star_rating"),
                    hotel_type=row.get("hotel_type"),
                    description=row.get("description"),
                    contact_phone=row.get("contact_phone"),
                    contact_email=row.get("contact_email"),
                    website=row.get("website"),
                    check_in_time=row.get("check_in_time"),
                    check_out_time=row.get("check_out_time"),
                    latitude=row.get("latitude"),
                    longitude=row.get("longitude"),
                    amenities=row.get("amenities"),
                    price_notes=row.get("price_notes"),
                    display_order=row.get("display_order") or 0
                )
                created.append(hotel.name)
        return Response({
            "created_count": len(created),
            "skipped_count": len(skipped),
            "created": created,
            "skipped": skipped
        })
