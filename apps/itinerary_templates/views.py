from rest_framework.viewsets import ModelViewSet
from .models import *
from .serializer import *
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import DayTourPermission
from django.db import transaction
import pandas as pd
from rest_framework import status
from apps.geography.models import Country

class ItineraryTemplateViewSet(ModelViewSet):
    queryset = ItineraryTemplate.objects.all()
    serializer_class = ItineraryTemplateSerializer
    permission_classes = [DayTourPermission]

    def get_queryset(self):
        queryset = ItineraryTemplate.objects.filter(deleted_at__isnull=True,is_active=True)
        country = self.request.query_params.get("country")
        region=self.request.query_params.get("region")
        total_days = self.request.query_params.get("total_days")
        if country:
            queryset = queryset.filter(country_id=country)
        if region:
            queryset=queryset.filter(days__day_tour__region_id=region)
        if total_days:
            queryset = queryset.filter(total_days=total_days)
        queryset = queryset.order_by("-is_default", "id")
        return queryset

    def perform_create(self, serializer):
        with transaction.atomic():
            serializer.save(created_by=self.request.user,total_days=1,total_nights=1,)

    @action(detail=True, methods=["post"])
    def add_day(self, request, pk=None):
        template = self.get_object()
        serializer = ItineraryTemplateDaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(template=template)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def attach_inclusion(self, request, pk=None):
        template = self.get_object()
        incl_id = request.data.get("incl_excl")
        obj, created = ItineraryTemplateInclExcl.objects.get_or_create(
            template=template,incl_excl_id=incl_id)

        return Response({
            "attached": created
        })    
    
    @action(detail=True, methods=["post"])
    def remove_inclusion(self, request, pk=None):
        template = self.get_object()
        incl_id = request.data.get("incl_excl")
        deleted, _ = ItineraryTemplateInclExcl.objects.filter(
            template=template,incl_excl_id=incl_id).delete()

        return Response({
            "deleted": deleted
        })
    
    @action(detail=False, methods=["post"], url_path="bulk-upload")
    def bulk_upload(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "Excel file required"}, status=400)
        df = pd.read_excel(file)
        created = []
        skipped = []
        errors = []
        for index, row in df.iterrows():
            try:
                with transaction.atomic():
                    country = Country.objects.filter(
                        code__iexact=str(row["country_code"]).strip()
                    ).first()
                    if not country:
                        errors.append(f"Row {index+1}: Country not found")
                        continue
                    exists = ItineraryTemplate.objects.filter(
                        country=country,
                        total_days=row["total_days"],
                    ).exists()
                    if exists:
                        skipped.append(
                            f"{row['country_code']} - {row['total_days']} days already exists"
                        )
                        continue
                    obj = ItineraryTemplate.objects.create(
                        country=country,
                        name=row["name"],
                        total_nights=1,
                        total_days=1,
                        description=row.get("description", ""),
                        is_default=str(row.get("is_default", "FALSE")).upper() == "TRUE",
                        created_by=request.user,
                    )
                    created.append(obj.code)
            except Exception as e:
                errors.append(f"Row {index+1}: {str(e)}")
        return Response(
            {
                "created_count": len(created),
                "created_templates": created,
                "skipped_count": len(skipped),
                "skipped_templates": skipped,
                "errors": errors,
            }
        )

class ItineraryTemplateDayViewSet(ModelViewSet):
    queryset = ItineraryTemplateDay.objects.all()
    serializer_class = ItineraryTemplateDaySerializer
    permission_classes = [DayTourPermission]

    @action(detail=False, methods=["post"], url_path="bulk-upload-template-days")
    def bulk_upload_template_days(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "Excel file required"}, status=400)
        try:
            df = pd.read_excel(file, header=0)
            df = df.iloc[1:]  
            df.columns = df.columns.str.strip()
        except Exception as e:
            return Response({"error": str(e)}, status=400)
        created, skipped, errors = [], [], []
        for index, row in df.iterrows():
            try:
                template_code = str(row["template_code"]).strip()
                day_tour_code = str(row["day_tour_code"]).strip()
                day_num = row["day_number"]
                template = ItineraryTemplate.objects.filter(code__iexact=template_code).first()
                if not template:
                    errors.append(f"Row {index+2}: Template not found ({template_code})")
                    continue
                day_tour = DayTour.objects.filter(unique_code__iexact=day_tour_code).first()
                if not day_tour:
                    errors.append(f"Row {index+2}: DayTour not found ({day_tour_code})")
                    continue
                if ItineraryTemplateDay.objects.filter(template=template, day_number=day_num).exists():
                    skipped.append(f"{template_code} day {day_num} already exists")
                    continue
                obj = ItineraryTemplateDay.objects.create(
                    template=template,
                    day_number=day_num,
                    day_tour=day_tour,
                    custom_notes=row.get("custom_notes", ""),
                    is_arrival_day=str(row.get("is_arrival_day", "FALSE")).upper() == "TRUE",
                    is_departure_day=str(row.get("is_departure_day", "FALSE")).upper() == "TRUE",
                    display_order=row.get("display_order", 0),
                )
                created.append(obj.id)
            except Exception as e:
                errors.append(f"Row {index+2}: {str(e)}")
        return Response({
            "created_count": len(created),
            "created_days": created,
            "skipped_count": len(skipped),
            "skipped_days": skipped,
            "errors": errors,
        })
    
class ItineraryTemplateInclExclViewSet(ModelViewSet):
    queryset = ItineraryTemplateInclExcl.objects.all()
    serializer_class = ItineraryTemplateInclExclSerializer
    permission_classes = [DayTourPermission]

    @action(detail=False,methods=["post"],url_path="bulk-upload-template-incl-excl")
    def bulk_upload_template_incl_excl(self,request):
        file=request.FILES.get("file")
        if not file:
            return Response({"error":"Excel file required"},status=400)
        df=pd.read_excel(file,header=0)
        df=df.iloc[1:]
        df.columns=df.columns.str.strip()
        created=[]
        skipped=[]
        errors=[]
        for i,row in df.iterrows():
            try:
                template_code=str(row["template_code"]).strip()
                incl_code=str(row["incl_excl_code"]).strip()
                template=ItineraryTemplate.objects.filter(code__iexact=template_code).first()
                if not template:
                    errors.append(f"Row {i+2}:Template not found ({template_code})")
                    continue
                incl=InclusionExclusion.objects.filter(unique_code__iexact=incl_code).first()
                if not incl:
                    errors.append(f"Row {i+2}:InclExcl not found ({incl_code})")
                    continue
                obj,created_flag=ItineraryTemplateInclExcl.objects.get_or_create(template=template,incl_excl=incl)
                if created_flag:
                    created.append(incl_code)
                else:
                    skipped.append(incl_code)
            except Exception as e:
                errors.append(f"Row {i+2}:{str(e)}")
        return Response({
            "created_count":len(created),
            "created_items":created,
            "skipped_count":len(skipped),
            "skipped_items":skipped,
            "errors":errors
        })  