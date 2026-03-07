from django.db.models import Q
from django.db import transaction
from django.http import HttpResponse
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import UserPlan, UserPlanDay, UserPlanInclExcl
from .serializer import UserPlanSerializer, UserPlanDaySerializer, UserPlanInclExclSerializer
from .utils import generate_plan_number, generate_share_token
from common.permissions import DayTourPermission, UserPlanPermission
from common.constant import UserRoletype, PLAN_STATUS
from apps.itinerary_templates.models import ItineraryTemplate
from apps.geography.models import Region
from apps.inclusions.models import InclusionExclusion
import io


def _distribute_days(total_days, num_cities):
    """
    Evenly distribute total_days across num_cities.
    Remainder days are assigned to earlier cities.

    Example: 5 days, 2 cities → [3, 2]
    Example: 6 days, 3 cities → [2, 2, 2]
    """
    base = total_days // num_cities
    remainder = total_days % num_cities
    return [base + (1 if i < remainder else 0) for i in range(num_cities)]


class UserPlanViewSet(ModelViewSet):
    serializer_class = UserPlanSerializer
    permission_classes = [UserPlanPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["country", "status", "user"]
    search_fields = ["name", "plan_number", "user__name", "user__email", "client_name", "country__name"]

    def get_queryset(self):
        user = self.request.user
        if user.role == UserRoletype.SUPER_ADMIN or user.is_superuser:
            return UserPlan.objects.all().order_by("-id")
        if user.role == UserRoletype.AGENT:
            return UserPlan.objects.filter(
                Q(user=user) | Q(user__created_by=user)
            ).order_by("-id")
        return UserPlan.objects.filter(user=user).order_by("-id")

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            plan_number=generate_plan_number(),
            share_token=generate_share_token()
        )

    @action(detail=False, methods=["post"])
    def auto_generate_draft(self, request):
        """
        Auto-generate a draft plan from city allocations.

        Request body:
        {
            "country": <id>,
            "total_days": 5,
            "start_date": "2025-06-10",   // optional
            "travel_type": "COUPLE",       // optional
            "city_allocations": [
                {"region": <id>, "days": 3},
                {"region": <id>, "days": 2}
            ]
        }

        Logic:
        1. Validate total_days == sum of allocation days
        2. Create UserPlan (DRAFT)
        3. For each city, load its default template (region + is_default + is_active)
        4. Create UserPlanDay rows linked to region + template + day_tour
        5. Return the full plan
        """
    @action(detail=False, methods=["post"])
    def auto_generate_draft(self, request):
        print("====== AUTO GENERATE DRAFT REACHED ======")
        try:
            print("REQUEST BODY:", request.body)
        except Exception as e:
            print("COULD NOT READ BODY:", e)
        try:
            country_id = request.data.get("country")
            total_days = request.data.get("total_days")
            start_date = request.data.get("start_date")
            travel_type = request.data.get("travel_type")
            city_allocations = request.data.get("city_allocations", [])

            if not country_id or not total_days or not city_allocations:
                return Response(
                    {"error": "country, total_days, and city_allocations are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            allocated_total = sum(a.get("days", 0) for a in city_allocations)
            if allocated_total != int(total_days):
                return Response(
                    {"error": f"city_allocations sum ({allocated_total}) must equal total_days ({total_days})."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                plan = UserPlan.objects.create(
                    user=request.user,
                    country_id=country_id,
                    name=f"Trip Plan",
                    total_days=int(total_days),
                    total_nights=int(total_days) - 1,
                    start_date=start_date or None,
                    status=PLAN_STATUS.DRAFT,
                    plan_number=generate_plan_number(),
                    share_token=generate_share_token(),
                )

                day_number = 1
                for alloc in city_allocations:
                    region_id = alloc.get("region")
                    days_count = int(alloc.get("days", 0))
                    if not region_id or days_count <= 0:
                        continue

                    # Find the default single-day template for this region
                    tmpl_qs = ItineraryTemplate.objects.filter(
                        region_id=region_id,
                        is_default=True,
                        is_active=True,
                        deleted_at__isnull=True,
                    )
                    if travel_type:
                        typed = tmpl_qs.filter(
                            Q(travel_type=travel_type) | Q(travel_type__isnull=True)
                        )
                        tmpl_qs = typed if typed.exists() else tmpl_qs

                    default_template = tmpl_qs.first()

                    # Get the day_tour from the template's day entry (day_number=1)
                    default_day_tour = None
                    if default_template:
                        tmpl_day = default_template.days.filter(day_number=1).first()
                        default_day_tour = tmpl_day.day_tour if tmpl_day else None

                    for _ in range(days_count):
                        UserPlanDay.objects.create(
                            user_plan=plan,
                            day_number=day_number,
                            region_id=region_id,
                            template=default_template,
                            day_tour=default_day_tour,
                        )
                        day_number += 1

                # Auto-attach all active inclusions/exclusions for this country
                country_ie = InclusionExclusion.objects.filter(
                    country_id=country_id,
                    is_active=True,
                    deleted_at__isnull=True,
                )
                for ie in country_ie:
                    UserPlanInclExcl.objects.create(
                        user_plan=plan,
                        incl_excl=ie,
                    )

            serializer = UserPlanSerializer(plan)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            import traceback
            return Response(
                {"error": "Failed to generate draft.", "traceback": traceback.format_exc()},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"])
    def finalize(self, request, pk=None):
        """Convert a DRAFT plan to CONFIRMED (finalized by user)."""
        plan = self.get_object()
        if plan.status.upper() not in (PLAN_STATUS.DRAFT, "DRAFT"):
            return Response(
                {"error": f"Plan is already {plan.status}. Only DRAFT plans can be finalized."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        plan.status = PLAN_STATUS.CONFIRMED
        plan.save(update_fields=["status"])
        serializer = UserPlanSerializer(plan)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def export_pdf(self, request, pk=None):
        """
        Export a plan as a PDF using reportlab (pure Python, no native dependencies).
        Returns a PDF file download.
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import mm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
        except ImportError:
            return Response(
                {"error": "reportlab is not installed. Run: pip install reportlab"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        plan = self.get_object()
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=20, spaceAfter=4, textColor=colors.HexColor("#1e293b"))
        sub_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=11, textColor=colors.HexColor("#64748b"), spaceAfter=12)
        section_style = ParagraphStyle("Section", parent=styles["Heading2"], fontSize=13, spaceBefore=14, spaceAfter=6, textColor=colors.HexColor("#4f46e5"))
        body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14, textColor=colors.HexColor("#334155"))

        story = []
        story.append(Paragraph(f"Itinerary: {plan.name}", title_style))
        story.append(Paragraph(f"Plan # {plan.plan_number} &nbsp;&bull;&nbsp; {plan.total_days} Days / {plan.total_nights} Nights &nbsp;&bull;&nbsp; Status: {plan.status}", sub_style))
        if plan.start_date:
            story.append(Paragraph(f"Start Date: {plan.start_date}", sub_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceAfter=10))

        # City groups
        serializer = UserPlanSerializer(plan)
        city_groups = serializer.data.get("city_groups", [])
        if city_groups:
            story.append(Paragraph("Cities Overview", section_style))
            city_data = [["City", "Days"]]
            for g in city_groups:
                city_data.append([g["region_name"], f"{g['days_count']} day(s)"])
            t = Table(city_data, colWidths=[120*mm, 50*mm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#4f46e5")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE", (0,0), (-1,-1), 10),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#f8fafc"), colors.white]),
                ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0,0), (-1,-1), 6),
                ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 10))

        # Day-by-day itinerary
        story.append(Paragraph("Day-by-Day Itinerary", section_style))
        sorted_days = sorted(plan.days.all(), key=lambda d: d.day_number)
        for day in sorted_days:
            region_label = day.region.name if day.region else ""
            tmpl_label = day.template.name if day.template else ""
            tour_text = day.day_tour.activity_combination if day.day_tour else "—"
            notes = day.day_tour.itinerary_text if day.day_tour else ""

            day_data = [
                [Paragraph(f"<b>Day {day.day_number}</b>", body_style), Paragraph(f"<b>{region_label}</b>", body_style)],
                [Paragraph(tour_text, body_style), Paragraph(tmpl_label, body_style)],
            ]
            if notes:
                day_data.append([Paragraph(notes, ParagraphStyle("notes", parent=body_style, textColor=colors.HexColor("#64748b"))), ""])

            t = Table(day_data, colWidths=[100*mm, 70*mm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f1f5f9")),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0,0), (-1,-1), 5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 5),
                ("SPAN", (0,2), (-1,2)),
            ]))
            story.append(t)
            story.append(Spacer(1, 4))

        doc.build(story)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="itinerary_{plan.plan_number}.pdf"'
        return response

    @action(detail=True, methods=["post"])
    def clone(self, request, pk=None):
        old = self.get_object()
        new_plan = UserPlan.objects.create(
            user=request.user,
            country=old.country,
            name=old.name + " Copy",
            total_days=old.total_days,
            total_nights=old.total_nights,
            plan_number=generate_plan_number(),
            share_token=generate_share_token()
        )
        for d in old.days.all():
            UserPlanDay.objects.create(
                user_plan=new_plan,
                day_number=d.day_number,
                region=d.region,
                template=d.template,
                day_tour=d.day_tour,
                custom_itinerary_text=d.custom_itinerary_text,
                notes=d.notes,
            )
        for i in old.incl_excl.all():
            UserPlanInclExcl.objects.create(user_plan=new_plan, incl_excl=i.incl_excl)
        return Response({"message": "Plan cloned successfully", "new_plan_id": new_plan.id})


class UserPlanDayViewSet(ModelViewSet):
    serializer_class = UserPlanDaySerializer
    permission_classes = [UserPlanPermission]

    def get_queryset(self):
        user = self.request.user
        if user.role == UserRoletype.SUPER_ADMIN or user.is_superuser:
            return UserPlanDay.objects.all()
        return UserPlanDay.objects.filter(user_plan__user=user)


class UserPlanInclExclViewSet(ModelViewSet):
    serializer_class = UserPlanInclExclSerializer
    permission_classes = [UserPlanPermission]

    def get_queryset(self):
        user = self.request.user
        if user.role == UserRoletype.SUPER_ADMIN or user.is_superuser:
            return UserPlanInclExcl.objects.all()
        return UserPlanInclExcl.objects.filter(user_plan__user=user)