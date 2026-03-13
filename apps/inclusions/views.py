from rest_framework.viewsets import ModelViewSet
from .models import InclExclCategory,InclusionExclusion
from .serializer import InclExclCategorySerializer,InclusionExclusionSerializer
from rest_framework.decorators import action
from collections import defaultdict
from rest_framework.response import Response
from common.permissions import DayTourPermission
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from apps.geography.models import Country
import pandas as pd

class InclExclCategoryViewSet(ModelViewSet):
    queryset = InclExclCategory.objects.filter(is_active=True).order_by("display_order")
    serializer_class = InclExclCategorySerializer
    permission_classes = [DayTourPermission]

class InclusionExclusionViewSet(ModelViewSet):
    serializer_class = InclusionExclusionSerializer
    permission_classes = [DayTourPermission]

    def get_queryset(self):
        qs = InclusionExclusion.objects.filter(is_active=True)
        country = self.request.query_params.get("country")
        type_val = self.request.query_params.get("type")
        category = self.request.query_params.get("category")

        if country:
            qs = qs.filter(country_id=country)
        if type_val:
            qs = qs.filter(type=type_val)
        if category:
            qs = qs.filter(category_id=category)

        return qs.order_by("display_order")

    @action(detail=False, methods=["get"], url_path="grouped")
    def grouped(self, request):
        country = request.query_params.get("country")
        if not country: 
            return Response({"error": "country required"}, status=400)
        qs = InclusionExclusion.objects.filter(country_id=country,is_active=True).select_related("category")

        data = {
            "INCLUSION": defaultdict(list),
            "EXCLUSION": defaultdict(list)
        }

        for item in qs:
            data[item.type][item.category.name].append({
                "id": item.id,
                "service": item.item_service,
                "notes": item.details_notes
            })

        return Response(data)

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
        required_cols = {"country_code", "unique_code", "type", "category", "item_service"}
        if not required_cols.issubset(set(df.columns)):
            return Response({"error": f"Missing required columns: {', '.join(required_cols - set(df.columns))}"}, status=400)

        # Drop description/instructions rows
        desc_mask = df.apply(
            lambda row: row.astype(str).str.upper().str.startswith(("REQUIRED", "OPTIONAL")).any(), axis=1
        )
        df = df[~desc_mask]

        country_map = {c.code.upper(): c for c in Country.objects.all()}
        # Category map: name (lower) → InclExclCategory
        cat_map = {c.name.strip().lower(): c for c in InclExclCategory.objects.all()}
        # Existing unique codes to detect duplicates
        existing_codes = set(InclusionExclusion.objects.values_list("unique_code", flat=True))

        records = df.to_dict("records")
        created_count = 0
        skipped = 0
        errors = []

        def _str(v):
            return str(v).strip() if v is not None and not (isinstance(v, float) and pd.isna(v)) else None
        def _int(v, default=0):
            try:
                return int(v) if v is not None and not (isinstance(v, float) and pd.isna(v)) else default
            except (ValueError, TypeError):
                return default

        with transaction.atomic():
            for idx, row in enumerate(records, start=2):
                country_code = str(row.get("country_code") or "").strip().upper()
                unique_code = _str(row.get("unique_code"))
                type_val = str(row.get("type") or "").strip().upper()
                category_name = _str(row.get("category"))
                item_service = _str(row.get("item_service"))

                if not item_service:
                    errors.append(f"Row {idx}: Missing item_service — skipped")
                    skipped += 1
                    continue
                if not unique_code:
                    errors.append(f"Row {idx}: Missing unique_code — skipped")
                    skipped += 1
                    continue
                if type_val not in ("INCLUSION", "EXCLUSION"):
                    errors.append(f"Row {idx}: type must be INCLUSION or EXCLUSION, got '{type_val}' — skipped")
                    skipped += 1
                    continue

                country = country_map.get(country_code)
                if not country:
                    errors.append(f"Row {idx}: Unknown country code '{country_code}' — skipped")
                    skipped += 1
                    continue

                if unique_code in existing_codes:
                    errors.append(f"Row {idx}: Duplicate unique_code '{unique_code}' — skipped")
                    skipped += 1
                    continue

                # Get or create the category
                if not category_name:
                    errors.append(f"Row {idx}: Missing category — skipped")
                    skipped += 1
                    continue
                cat_key = category_name.lower()
                if cat_key not in cat_map:
                    cat_obj = InclExclCategory.objects.create(name=category_name, is_active=True)
                    cat_map[cat_key] = cat_obj
                category = cat_map[cat_key]

                InclusionExclusion.objects.create(
                    country=country,
                    unique_code=unique_code,
                    type=type_val,
                    category=category,
                    item_service=item_service,
                    details_notes=_str(row.get("details_notes")),
                    source_files=_str(row.get("source_files")),
                    display_order=_int(row.get("display_order")),
                    is_active=True,
                )
                existing_codes.add(unique_code)
                created_count += 1

        return Response({
            "total_file_records": len(records),
            "created": created_count,
            "skipped": skipped,
            "errors": errors[:20],
        })

