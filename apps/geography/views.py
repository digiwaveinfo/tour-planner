from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .models import Country, Region
from .serializer import CountrySerializer, RegionSerializer
from common.permissions import *
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
import pandas as pd
import re


def _parse_star_rating(raw):
    """Extract integer star rating from strings like '5', '4-star', '3-star'."""
    if raw is None:
        return 3
    m = re.search(r'\d+', str(raw))
    return max(1, min(5, int(m.group()))) if m else 3


class CountryViewSet(ModelViewSet):
    queryset = Country.objects.filter(deleted_at__isnull=True)
    serializer_class = CountrySerializer
    permission_classes = [IsSuperAdminOrAdminWriteElseReadOnly]
    parser_classes = [MultiPartParser, FormParser]

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
        if "name" not in df.columns or "code" not in df.columns:
            return Response({"error": "Missing required columns: name, code"}, status=400)

        # Drop the description/instructions row (cells start with REQUIRED or OPTIONAL)
        desc_mask = df.apply(
            lambda row: row.astype(str).str.upper().str.startswith(("REQUIRED", "OPTIONAL")).any(), axis=1
        )
        df = df[~desc_mask]

        records = df.to_dict("records")
        created_count = 0
        skipped = 0
        errors = []
        to_create = []

        with transaction.atomic():
            for idx, row in enumerate(records, start=2):
                name = row.get("name")
                code = row.get("code")
                if not name or (isinstance(name, float) and pd.isna(name)):
                    errors.append(f"Row {idx}: Missing name — skipped")
                    skipped += 1
                    continue
                if not code or (isinstance(code, float) and pd.isna(code)):
                    errors.append(f"Row {idx}: Missing code — skipped")
                    skipped += 1
                    continue

                name = str(name).strip()
                code = str(code).strip().upper()
                iso_raw = row.get("iso_code")
                iso_code = str(iso_raw).strip() if iso_raw and not (isinstance(iso_raw, float) and pd.isna(iso_raw)) else None

                if Country.objects.filter(code=code).exists():
                    errors.append(f"Row {idx}: Country code '{code}' already exists — skipped")
                    skipped += 1
                    continue

                to_create.append(Country(name=name, code=code, iso_code=iso_code or None, is_active=True))

            if to_create:
                Country.objects.bulk_create(to_create, batch_size=1000)
                created_count = len(to_create)

        return Response({
            "total_file_records": len(records),
            "created": created_count,
            "skipped": skipped,
            "errors": errors[:20],
        })


class RegionViewSet(ModelViewSet):
    serializer_class = RegionSerializer
    permission_classes = [IsSuperAdminOrAdminWriteElseReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        qs = Region.objects.select_related("country").filter(deleted_at__isnull=True)
        country_id = self.request.query_params.get("country")
        if country_id:
            qs = qs.filter(country_id=country_id)
        return qs

    @action(detail=True, methods=["get"])
    def regions(self, request, pk=None):
        regions = Region.objects.filter(country_id=pk)
        serializer = RegionSerializer(regions, many=True)
        return Response(serializer.data)

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
        required = {"country_code", "name"}
        if not required.issubset(set(df.columns)):
            return Response({"error": "Missing required columns: country_code, name"}, status=400)

        desc_mask = df.apply(
            lambda row: row.astype(str).str.upper().str.startswith(("REQUIRED", "OPTIONAL")).any(), axis=1
        )
        df = df[~desc_mask]

        country_map = {c.code.upper(): c for c in Country.objects.all()}
        records = df.to_dict("records")
        created_count = 0
        skipped = 0
        errors = []
        used_codes = {}  # country_code -> set of codes used this batch

        with transaction.atomic():
            for idx, row in enumerate(records, start=2):
                country_code = str(row.get("country_code") or "").strip().upper()
                name = row.get("name")
                if not name or (isinstance(name, float) and pd.isna(name)):
                    errors.append(f"Row {idx}: Missing name — skipped")
                    skipped += 1
                    continue
                name = str(name).strip()

                country = country_map.get(country_code)
                if not country:
                    errors.append(f"Row {idx}: Unknown country code '{country_code}' — skipped")
                    skipped += 1
                    continue

                code_raw = row.get("code", "")
                code = str(code_raw).strip().upper() if code_raw and not (isinstance(code_raw, float) and pd.isna(code_raw)) else ""
                if not code:
                    # Auto-generate from name
                    base = re.sub(r"[^A-Za-z0-9]", "", name).upper()[:10] or "REGION"
                    code = base
                    db_codes = set(Region.objects.filter(country=country).values_list("code", flat=True))
                    batch_codes = used_codes.get(country_code, set())
                    suffix = 1
                    while code in db_codes or code in batch_codes:
                        code = f"{base[:8]}{suffix:02d}"
                        suffix += 1

                used_codes.setdefault(country_code, set()).add(code)

                desc = row.get("description")
                description = str(desc).strip() if desc and not (isinstance(desc, float) and pd.isna(desc)) else None
                try:
                    display_order = int(row.get("display_order") or 0)
                except (ValueError, TypeError):
                    display_order = 0

                if Region.objects.filter(country=country, name=name).exists():
                    errors.append(f"Row {idx}: Region '{name}' already exists in '{country_code}' — skipped")
                    skipped += 1
                    continue

                Region.objects.create(
                    country=country,
                    name=name,
                    code=code,
                    description=description,
                    display_order=display_order,
                    is_active=True,
                )
                created_count += 1

        return Response({
            "total_file_records": len(records),
            "created": created_count,
            "skipped": skipped,
            "errors": errors[:20],
        })
