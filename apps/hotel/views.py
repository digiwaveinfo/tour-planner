from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Hotel, HotelImage
from .serializer import HotelSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import *
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from apps.geography.models import Country, Region
import pandas as pd
import re

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

    def update(self, request, *args, **kwargs):
        images = request.FILES.getlist("images")
        remove_images = request.data.getlist("remove_images") if hasattr(request.data, 'getlist') else request.data.get("remove_images", [])
        if isinstance(remove_images, str):
            remove_images = [remove_images]

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        hotel = serializer.save()

        if remove_images:
            HotelImage.objects.filter(
                id__in=[int(i) for i in remove_images],
                hotel=hotel
            ).delete()

        for img in images:
            HotelImage.objects.create(hotel=hotel, image=img)

        return Response(self.get_serializer(hotel).data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

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
        required_cols = {"country_code", "region", "name"}
        if not required_cols.issubset(set(df.columns)):
            return Response({"error": f"Missing required columns: {', '.join(required_cols)}"}, status=400)

        # Drop description/instructions row
        desc_mask = df.apply(
            lambda row: row.astype(str).str.upper().str.startswith(("REQUIRED", "OPTIONAL")).any(), axis=1
        )
        df = df[~desc_mask]

        country_map = {c.code.upper(): c for c in Country.objects.all()}
        region_map = {(r.country_id, r.name.strip().lower()): r for r in Region.objects.select_related("country")}
        # Also normalised (accent-stripped) lookup
        import unicodedata
        def _norm(s):
            s = s.strip().lower()
            return unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("ASCII")
        region_norm_map = {(r.country_id, _norm(r.name)): r for r in Region.objects.select_related("country")}

        records = df.to_dict("records")
        created_count = 0
        skipped = 0
        errors = []

        with transaction.atomic():
            for idx, row in enumerate(records, start=2):
                country_code = str(row.get("country_code") or "").strip().upper()
                region_raw = str(row.get("region") or "").strip()
                name = row.get("name")

                if not name or (isinstance(name, float) and pd.isna(name)):
                    errors.append(f"Row {idx}: Missing name — skipped")
                    skipped += 1
                    continue
                name = str(name).strip()

                country = country_map.get(country_code)
                if not country:
                    errors.append(f"Row {idx}: Unknown country '{country_code}' — skipped")
                    skipped += 1
                    continue

                region = region_map.get((country.id, region_raw.lower())) or \
                         region_norm_map.get((country.id, _norm(region_raw)))
                if not region:
                    # Auto-create region
                    auto_code = re.sub(r"[^A-Za-z0-9]", "", region_raw).upper()[:10] or "REGION"
                    existing = set(Region.objects.filter(country=country).values_list("code", flat=True))
                    code = auto_code
                    suffix = 1
                    while code in existing:
                        code = f"{auto_code[:8]}{suffix:02d}"
                        suffix += 1
                    region = Region.objects.create(country=country, name=region_raw, code=code, is_active=True)
                    region_map[(country.id, region_raw.lower())] = region
                    region_norm_map[(country.id, _norm(region_raw))] = region

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

                # star_rating may be '4-star' or numeric
                star_raw = row.get("star_rating", "3")
                m = re.search(r"\d+", str(star_raw)) if star_raw else None
                star_rating = max(1, min(5, int(m.group()))) if m else 3

                amenities_raw = _str(row.get("amenities"))
                amenities = [a.strip() for a in amenities_raw.split(",") if a.strip()] if amenities_raw else None

                # Parse price: support both explicit price+currency columns OR "ISK 40000" in price_notes
                VALID_CURRENCIES = {"INR", "USD", "EUR", "ISK", "CHF"}
                price_notes_raw = _str(row.get("price_notes")) or ""
                explicit_price = _str(row.get("price"))
                explicit_cur = str(row.get("currency") or "").strip().upper()

                if explicit_price is not None:
                    # Separate price and currency columns provided
                    price_currency = explicit_cur if explicit_cur in VALID_CURRENCIES else "INR"
                    try:
                        price_per_night = float(explicit_price) if explicit_price else 0
                    except (ValueError, TypeError):
                        price_per_night = 0
                else:
                    # Parse from price_notes column ("ISK 40000", "From CHF 450/night", etc.)
                    price_currency = "INR"
                    price_per_night = 0
                    if price_notes_raw:
                        for cur in VALID_CURRENCIES:
                            if cur in price_notes_raw.upper():
                                price_currency = cur
                                break
                        num_match = re.search(r"[\d]+(?:[.,]\d+)?", price_notes_raw.replace(",", ""))
                        if num_match:
                            try:
                                price_per_night = float(num_match.group())
                            except ValueError:
                                pass

                Hotel.objects.create(
                    name=name,
                    country=country,
                    region=region,
                    city=_str(row.get("city")),
                    address=_str(row.get("address")),
                    star_rating=star_rating,
                    hotel_type=_str(row.get("hotel_type")),
                    description=_str(row.get("description")),
                    contact_phone=_str(row.get("contact_phone")),
                    contact_email=_str(row.get("contact_email")),
                    website=_str(row.get("website")),
                    check_in_time=_str(row.get("check_in_time")),
                    check_out_time=_str(row.get("check_out_time")),
                    latitude=_dec(row.get("latitude")),
                    longitude=_dec(row.get("longitude")),
                    amenities=amenities,
                    price_per_night=price_per_night,
                    price_currency=price_currency,
                    price_notes=price_notes_raw or None,
                    display_order=_int(row.get("display_order")),
                    is_active=True,
                )
                created_count += 1

        return Response({
            "total_file_records": len(records),
            "created": created_count,
            "skipped": skipped,
            "errors": errors[:20],
        })
