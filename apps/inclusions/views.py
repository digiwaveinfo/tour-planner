from rest_framework.viewsets import ModelViewSet
from .models import InclExclCategory,InclusionExclusion
from .serializer import InclExclCategorySerializer,InclusionExclusionSerializer
from rest_framework.decorators import action
from collections import defaultdict
from rest_framework.response import Response
from common.permissions import DayTourPermission
import pandas as pd
from django.db import transaction
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser
from apps.geography.models import Country

class InclExclCategoryViewSet(ModelViewSet):
    queryset = InclExclCategory.objects.filter(is_active=True).order_by("display_order")
    serializer_class = InclExclCategorySerializer
    permission_classes = [DayTourPermission]
    parser_classes = [MultiPartParser, FormParser,JSONParser]

    @action(detail=False, methods=["post"], url_path="bulk-upload")
    def bulk_upload(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "file required"}, status=400)
        try:
            df = pd.read_excel(file)
        except:
            df = pd.read_csv(file)
        created=[]
        skipped=[]
        with transaction.atomic():
            for index,row in df.iterrows():
                name=str(row.get("name","")).strip()
                display=row.get("display_order") or 0
                if not name:
                    skipped.append({"row":index+1,"reason":"name missing"})
                    continue
                if InclExclCategory.objects.filter(name__iexact=name).exists():
                    skipped.append({"row":index+1,"reason":"duplicate"})
                    continue
                InclExclCategory.objects.create(
                    name=name,
                    display_order=display
                )
                created.append(name)
        return Response({
            "created":created,
            "skipped":skipped
        })

class InclusionExclusionViewSet(ModelViewSet):
    serializer_class = InclusionExclusionSerializer
    permission_classes = [DayTourPermission]
    parser_classes = [MultiPartParser, FormParser,JSONParser]

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
                type_val = str(row.get("type", "")).strip().upper()
                category_name = str(row.get("category_name", "")).strip()
                service = str(row.get("item_service", "")).strip()
                notes = str(row.get("details_notes", "")).strip()
                source = str(row.get("source_files", "")).strip()
                order = row.get("display_order") or 0
                if not country_code or not type_val or not category_name or not service:
                    skipped.append({"row": index + 1, "reason": "missing required fields"})
                    continue
                try:
                    country = Country.objects.get(code__iexact=country_code)
                except Country.DoesNotExist:
                    skipped.append({"row": index + 1, "reason": "country not found"})
                    continue
                try:
                    category = InclExclCategory.objects.get(name__iexact=category_name)
                except InclExclCategory.DoesNotExist:
                    skipped.append({"row": index + 1, "reason": "category not found"})
                    continue
                item = InclusionExclusion.objects.create(
                    country=country,
                    type=type_val,
                    category=category,
                    item_service=service,
                    details_notes=notes,
                    source_files=source,
                    display_order=order,
                )
                created.append(item.item_service)
        return Response({
            "created_count": len(created),
            "skipped_count": len(skipped),
            "created": created,
            "skipped": skipped,
        })
