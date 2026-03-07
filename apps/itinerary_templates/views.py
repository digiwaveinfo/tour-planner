from rest_framework.viewsets import ModelViewSet
from .models import (
    ItineraryTemplate,
    ItineraryTemplateDay as ItineraryTemplateDayModel,
    ItineraryTemplateInclExcl,
)
from .serializer import *
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from common.permissions import DayTourPermission
from django.db import transaction
from django.db.models import Q
import secrets


class ItineraryTemplateViewSet(ModelViewSet):
    queryset = ItineraryTemplate.objects.all()
    serializer_class = ItineraryTemplateSerializer
    permission_classes = [DayTourPermission]

    def get_queryset(self):
        queryset = ItineraryTemplate.objects.filter(
            deleted_at__isnull=True, is_active=True
        ).prefetch_related(
            "days__day_tour__tour_attractions__attraction",
            "incl_excl__incl_excl__category",
        ).select_related("country", "region")

        country = self.request.query_params.get("country")
        region = self.request.query_params.get("region")
        total_days = self.request.query_params.get("total_days")
        travel_type = self.request.query_params.get("travel_type")

        if country:
            queryset = queryset.filter(country_id=country)
        if region:
            queryset = queryset.filter(region_id=region)
        if total_days:
            queryset = queryset.filter(total_days=total_days)

        # Smart fallback: try type-specific first, fall back to all
        if travel_type:
            typed_qs = queryset.filter(
                Q(travel_type=travel_type) | Q(travel_type__isnull=True)
            )
            if typed_qs.exists():
                queryset = typed_qs

        queryset = queryset.order_by("-is_default", "id")
        return queryset

    @action(detail=False, methods=["get"])
    def available_days(self, request):
        """Return distinct total_days values for a country, with travel_type fallback."""
        qs = ItineraryTemplate.objects.filter(
            deleted_at__isnull=True, is_active=True
        )
        country = request.query_params.get("country")
        travel_type = request.query_params.get("travel_type")
        if country:
            qs = qs.filter(country_id=country)

        if travel_type:
            typed_qs = qs.filter(
                Q(travel_type=travel_type) | Q(travel_type__isnull=True)
            )
            if typed_qs.exists():
                qs = typed_qs

        days = sorted(qs.values_list("total_days", flat=True).distinct())
        return Response({"days": days})

    def _generate_code(self):
        while True:
            random_number = secrets.randbelow(900000) + 100000
            code = f"IT-{random_number}"
            if not ItineraryTemplate.objects.filter(code=code).exists():
                return code

    def perform_create(self, serializer):
        with transaction.atomic():
            generated_code = self._generate_code()
            serializer.save(created_by=self.request.user, code=generated_code)

    @action(detail=True, methods=["post"])
    def set_as_default(self, request, pk=None):
        """
        Mark this template as the default for its region.
        Clears the previous default for that region first.
        """
        template = self.get_object()
        if not template.region_id:
            return Response(
                {"error": "Template must have a region assigned to be set as default."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            # Clear existing default for this region
            ItineraryTemplate.objects.filter(
                region=template.region, is_default=True
            ).exclude(pk=template.pk).update(is_default=False)
            template.is_default = True
            template.save(update_fields=["is_default"])
        return Response({"is_default": True})

    @action(detail=True, methods=["post"])
    def add_day(self, request, pk=None):
        template = self.get_object()
        day_number = request.data.get("day_number")
        existing = ItineraryTemplateDayModel.objects.filter(
            template=template, day_number=day_number
        ).first()
        if existing:
            serializer = ItineraryTemplateDaySerializer(
                existing, data=request.data, partial=True
            )
        else:
            serializer = ItineraryTemplateDaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(template=template)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def attach_inclusion(self, request, pk=None):
        template = self.get_object()
        incl_id = request.data.get("incl_excl")
        obj, created = ItineraryTemplateInclExcl.objects.get_or_create(
            template=template, incl_excl_id=incl_id)
        return Response({"attached": created})

    @action(detail=True, methods=["post"])
    def remove_inclusion(self, request, pk=None):
        template = self.get_object()
        incl_id = request.data.get("incl_excl")
        deleted, _ = ItineraryTemplateInclExcl.objects.filter(
            template=template, incl_excl_id=incl_id).delete()
        return Response({"deleted": deleted})


class ItineraryTemplateDayViewSet(ModelViewSet):
    queryset = ItineraryTemplateDayModel.objects.all()
    serializer_class = ItineraryTemplateDaySerializer
    permission_classes = [DayTourPermission]

    def get_queryset(self):
        qs = ItineraryTemplateDayModel.objects.all()
        template = self.request.query_params.get("template")
        if template:
            qs = qs.filter(template_id=template)
        return qs.order_by("day_number")


class ItineraryTemplateInclExclViewSet(ModelViewSet):
    queryset = ItineraryTemplateInclExcl.objects.all()
    serializer_class = ItineraryTemplateInclExclSerializer
    permission_classes = [DayTourPermission]