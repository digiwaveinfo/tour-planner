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
        """Auto-generate a DRAFT plan from day_assignments (preferred) or city_allocations (fallback)."""
        try:
            country_id = request.data.get("country")
            total_days_raw = request.data.get("total_days")
            start_date = request.data.get("start_date")
            travel_type = request.data.get("travel_type")
            day_assignments = request.data.get("day_assignments", [])
            city_allocations = request.data.get("city_allocations", [])

            if not country_id or not total_days_raw:
                return Response(
                    {"error": "country and total_days are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                total_days = int(total_days_raw)
            except (TypeError, ValueError):
                return Response(
                    {"error": "total_days must be a valid integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if total_days <= 0:
                return Response(
                    {"error": "total_days must be greater than 0."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            normalized_day_assignments = []
            if day_assignments:
                try:
                    for idx, item in enumerate(day_assignments, start=1):
                        region_id = int(item.get("region"))
                        day_number = int(item.get("day_number", idx))
                        normalized_day_assignments.append({"day_number": day_number, "region": region_id})
                except (TypeError, ValueError, AttributeError):
                    return Response(
                        {"error": "day_assignments must be an array of objects with numeric day_number and region."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                normalized_day_assignments.sort(key=lambda d: d["day_number"])
                if len(normalized_day_assignments) != total_days:
                    return Response(
                        {"error": f"day_assignments count ({len(normalized_day_assignments)}) must equal total_days ({total_days})."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                expected_days = list(range(1, total_days + 1))
                actual_days = [d["day_number"] for d in normalized_day_assignments]
                if actual_days != expected_days:
                    return Response(
                        {"error": "day_assignments must contain a continuous day_number sequence starting at 1."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                if not city_allocations:
                    return Response(
                        {"error": "Provide either day_assignments or city_allocations."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                normalized_allocations = []
                try:
                    for alloc in city_allocations:
                        region_id = int(alloc.get("region"))
                        days_count = int(alloc.get("days", 0))
                        if days_count <= 0:
                            return Response(
                                {"error": "Each city allocation must have days greater than 0."},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                        normalized_allocations.append({"region": region_id, "days": days_count})
                except (TypeError, ValueError, AttributeError):
                    return Response(
                        {"error": "city_allocations must be an array of objects with numeric region and days fields."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                allocated_total = sum(a["days"] for a in normalized_allocations)
                if allocated_total != total_days:
                    return Response(
                        {"error": f"city_allocations sum ({allocated_total}) must equal total_days ({total_days})."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                day_number = 1
                for alloc in normalized_allocations:
                    for _ in range(alloc["days"]):
                        normalized_day_assignments.append({"day_number": day_number, "region": alloc["region"]})
                        day_number += 1

            region_ids = {d["region"] for d in normalized_day_assignments}
            valid_region_ids = set(
                Region.objects.filter(
                    id__in=region_ids,
                    country_id=country_id,
                    deleted_at__isnull=True,
                ).values_list("id", flat=True)
            )
            invalid_region_ids = sorted(region_ids - valid_region_ids)
            if invalid_region_ids:
                return Response(
                    {"error": f"Invalid regions for selected country: {invalid_region_ids}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                plan = UserPlan.objects.create(
                    user=request.user,
                    country_id=country_id,
                    name=f"Trip Plan",
                    total_days=total_days,
                    total_nights=total_days - 1,
                    start_date=start_date or None,
                    status=PLAN_STATUS.DRAFT,
                    plan_number=generate_plan_number(),
                    share_token=generate_share_token(),
                )

                template_cache = {}
                for day_item in normalized_day_assignments:
                    region_id = day_item["region"]
                    day_number = day_item["day_number"]

                    if region_id not in template_cache:
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
                        default_day_tour = None
                        if default_template:
                            tmpl_day = default_template.days.filter(day_number=1).first()
                            default_day_tour = tmpl_day.day_tour if tmpl_day else None

                        template_cache[region_id] = (default_template, default_day_tour)

                    default_template, default_day_tour = template_cache[region_id]
                    UserPlanDay.objects.create(
                        user_plan=plan,
                        day_number=day_number,
                        region_id=region_id,
                        template=default_template,
                        day_tour=default_day_tour,
                    )

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
        Export a beautifully formatted plan PDF with itinerary, pricing,
        inclusions/exclusions and terms & conditions.
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import mm
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                HRFlowable, KeepTogether, PageBreak,
            )
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        except ImportError:
            return Response(
                {"error": "reportlab is not installed. Run: pip install reportlab"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        plan = self.get_object()
        serializer = UserPlanSerializer(plan)
        plan_data = serializer.data
        buffer = io.BytesIO()

        # ── colours ──
        BRAND   = colors.HexColor("#4f46e5")
        BRAND_L = colors.HexColor("#eef2ff")
        DARK    = colors.HexColor("#1e293b")
        MID     = colors.HexColor("#475569")
        LIGHT   = colors.HexColor("#94a3b8")
        BORDER  = colors.HexColor("#e2e8f0")
        BG_EVEN = colors.HexColor("#f8fafc")
        WHITE   = colors.white
        GREEN   = colors.HexColor("#16a34a")
        GREEN_L = colors.HexColor("#f0fdf4")
        RED     = colors.HexColor("#dc2626")
        RED_L   = colors.HexColor("#fef2f2")
        CITY_PALETTE = [
            colors.HexColor("#4f46e5"), colors.HexColor("#e11d48"),
            colors.HexColor("#d97706"), colors.HexColor("#059669"),
            colors.HexColor("#0284c7"), colors.HexColor("#7c3aed"),
        ]

        page_w = A4[0] - 40 * mm          # usable width
        col_full = page_w

        # ── styles ──
        styles = getSampleStyleSheet()
        S = lambda name, **kw: ParagraphStyle(name, parent=styles["Normal"], **kw)

        s_title    = S("t", fontSize=22, leading=26, textColor=DARK, fontName="Helvetica-Bold")
        s_subtitle = S("st", fontSize=11, leading=15, textColor=MID)
        s_section  = S("sec", fontSize=14, leading=18, textColor=BRAND, fontName="Helvetica-Bold", spaceBefore=16, spaceAfter=6)
        s_body     = S("bd", fontSize=9.5, leading=13, textColor=DARK)
        s_body_sm  = S("bsm", fontSize=8.5, leading=12, textColor=MID)
        s_body_b   = S("bb", fontSize=9.5, leading=13, textColor=DARK, fontName="Helvetica-Bold")
        s_white_b  = S("wb", fontSize=10, leading=14, textColor=WHITE, fontName="Helvetica-Bold")
        s_center   = S("ctr", fontSize=9, leading=12, textColor=MID, alignment=TA_CENTER)
        s_right_b  = S("rb", fontSize=10, leading=14, textColor=DARK, fontName="Helvetica-Bold", alignment=TA_RIGHT)
        s_terms    = S("trm", fontSize=8, leading=11, textColor=MID)
        s_city_h   = S("ch", fontSize=11, leading=14, textColor=WHITE, fontName="Helvetica-Bold")
        s_brand_sm = S("brsm", fontSize=9, leading=12, textColor=BRAND, fontName="Helvetica-Bold")

        story = []

        # ──────────────── HEADER ────────────────
        country_name = plan_data.get("country_name", "")

        story.append(Paragraph("Tour Planner", S("brand", fontSize=10, textColor=BRAND, fontName="Helvetica-Bold")))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(f"{plan.name}", s_title))
        story.append(Spacer(1, 2 * mm))

        meta_parts = []
        if plan.plan_number:
            meta_parts.append(f"<b>Plan #</b> {plan.plan_number}")
        meta_parts.append(f"<b>{plan.total_days} Days / {plan.total_nights} Nights</b>")
        if country_name:
            meta_parts.append(f"<b>{country_name}</b>")
        if plan.start_date:
            meta_parts.append(f"Starting {plan.start_date.strftime('%d %b %Y')}")
        story.append(Paragraph(" &nbsp;&bull;&nbsp; ".join(meta_parts), s_subtitle))
        story.append(Spacer(1, 2 * mm))

        if plan.client_name:
            story.append(Paragraph(f"<b>Guest:</b> {plan.client_name}" + (f" &nbsp;|&nbsp; {plan.client_email}" if plan.client_email else ""), s_body_sm))

        story.append(Spacer(1, 3 * mm))
        story.append(HRFlowable(width="100%", thickness=1.5, color=BRAND, spaceAfter=8))

        # ──────────────── ROUTE OVERVIEW ────────────────
        city_groups = plan_data.get("city_groups", [])
        if city_groups:
            story.append(Paragraph("Route Overview", s_section))
            route_data = [
                [Paragraph("<b>City</b>", s_white_b),
                 Paragraph("<b>Nights</b>", s_white_b),
                 Paragraph("<b>Days</b>", s_white_b)],
            ]
            for i, g in enumerate(city_groups):
                day_nums = g.get("day_numbers", [])
                day_range = f"Day {day_nums[0]}–{day_nums[-1]}" if len(day_nums) > 1 else f"Day {day_nums[0]}"
                route_data.append([
                    Paragraph(f"● {g['region_name']}", s_body_b),
                    Paragraph(str(g["days_count"]), s_body),
                    Paragraph(day_range, s_body),
                ])
            t = Table(route_data, colWidths=[col_full * 0.50, col_full * 0.20, col_full * 0.30])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BRAND),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, BG_EVEN]),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(t)
            story.append(Spacer(1, 6 * mm))

        # ──────────────── CITY-GROUPED ITINERARY ────────────────
        story.append(Paragraph("Day-by-Day Itinerary", s_section))
        story.append(Spacer(1, 2 * mm))

        sorted_days = sorted(plan.days.select_related(
            "region", "template", "day_tour", "hotel"
        ).prefetch_related("day_tour__tour_attractions__attraction").all(), key=lambda d: d.day_number)

        # Build city groups from actual day objects
        groups = []
        for day in sorted_days:
            rid = day.region_id
            rname = day.region.name if day.region else "Unknown"
            if groups and groups[-1]["region_id"] == rid:
                groups[-1]["days"].append(day)
            else:
                groups.append({"region_id": rid, "region_name": rname, "days": [day]})

        for gi, group in enumerate(groups):
            city_color = CITY_PALETTE[gi % len(CITY_PALETTE)]
            city_bg = colors.HexColor("#f1f5f9")
            nights = len(group["days"])

            # City header row
            city_header_data = [[
                Paragraph(f"{group['region_name']}  —  {nights} {'Night' if nights == 1 else 'Nights'}", s_city_h)
            ]]
            city_t = Table(city_header_data, colWidths=[col_full])
            city_t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), city_color),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("ROUNDEDCORNERS", [6, 6, 0, 0]),
            ]))

            # Day rows within this city
            day_rows = []
            for day in group["days"]:
                tour = day.day_tour
                region_label = day.region.name if day.region else ""
                activity = tour.activity_combination if tour else "Free Day"
                notes = tour.itinerary_text if tour else ""

                # Attractions
                attractions_list = []
                if tour:
                    for ta in tour.tour_attractions.all().order_by("visit_order"):
                        attractions_list.append(f"{ta.visit_order}. {ta.attraction.name}")

                price_str = ""
                if tour and tour.price and tour.price > 0:
                    price_str = f"{tour.currency or 'INR'} {tour.price:,.0f}"

                # Build multi-line day cell
                parts = [f"<b>Day {day.day_number}</b> &nbsp; <font color='#94a3b8'>|</font> &nbsp; <b>{activity}</b>"]
                if notes:
                    parts.append(f"<br/><font size='8' color='#64748b'>{notes[:300]}</font>")
                if attractions_list:
                    parts.append(f"<br/><font size='8' color='#4f46e5'>{'  •  '.join(attractions_list)}</font>")

                meta_bits = []
                if tour and tour.est_time_distance:
                    meta_bits.append(f"⏱ {tour.est_time_distance}")
                if tour and tour.overnight_location:
                    meta_bits.append(f"🏨 {tour.overnight_location}")
                if meta_bits:
                    parts.append(f"<br/><font size='7' color='#94a3b8'>{'  |  '.join(meta_bits)}</font>")

                day_rows.append([
                    Paragraph("".join(parts), s_body),
                    Paragraph(price_str, s_right_b),
                ])

            day_table = Table(day_rows, colWidths=[col_full * 0.78, col_full * 0.22])
            day_table.setStyle(TableStyle([
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, BG_EVEN]),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (0, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))

            story.append(KeepTogether([city_t, day_table]))
            story.append(Spacer(1, 5 * mm))

        # ──────────────── PRICING SUMMARY ────────────────
        story.append(Paragraph("Pricing Summary", s_section))
        price_rows = [
            [Paragraph("<b>Day</b>", s_white_b),
             Paragraph("<b>Activity</b>", s_white_b),
             Paragraph("<b>City</b>", s_white_b),
             Paragraph("<b>Amount</b>", s_white_b)],
        ]
        grand_total = 0
        for day in sorted_days:
            tour = day.day_tour
            price_val = float(tour.price) if tour and tour.price else 0
            grand_total += price_val
            currency = tour.currency if tour else "INR"
            price_rows.append([
                Paragraph(f"Day {day.day_number}", s_body),
                Paragraph(tour.activity_combination if tour else "—", s_body),
                Paragraph(day.region.name if day.region else "—", s_body),
                Paragraph(f"{currency or 'INR'} {price_val:,.0f}" if price_val > 0 else "—", s_body),
            ])
        # Total row
        price_rows.append([
            Paragraph("", s_body), Paragraph("", s_body),
            Paragraph("<b>Grand Total</b>", s_body_b),
            Paragraph(f"<b>INR {grand_total:,.0f}</b>", S("gt", fontSize=11, textColor=BRAND, fontName="Helvetica-Bold", alignment=TA_RIGHT)),
        ])

        pt = Table(price_rows, colWidths=[col_full * 0.12, col_full * 0.40, col_full * 0.23, col_full * 0.25])
        pt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [WHITE, BG_EVEN]),
            ("BACKGROUND", (0, -1), (-1, -1), BRAND_L),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(pt)
        story.append(Spacer(1, 8 * mm))

        # ──────────────── INCLUSIONS / EXCLUSIONS ────────────────
        incl_excl_qs = plan.incl_excl.select_related("incl_excl__category").all()
        inclusions = [ie for ie in incl_excl_qs if ie.incl_excl.type == "INCLUSION"]
        exclusions = [ie for ie in incl_excl_qs if ie.incl_excl.type == "EXCLUSION"]

        if inclusions:
            story.append(Paragraph("What's Included", s_section))
            inc_rows = [[
                Paragraph("<b>#</b>", s_white_b),
                Paragraph("<b>Inclusion</b>", s_white_b),
                Paragraph("<b>Category</b>", s_white_b),
            ]]
            for idx, ie in enumerate(inclusions, 1):
                inc_rows.append([
                    Paragraph(str(idx), s_body),
                    Paragraph(ie.incl_excl.item_service, s_body),
                    Paragraph(ie.incl_excl.category.name if ie.incl_excl.category else "", s_body_sm),
                ])
            it = Table(inc_rows, colWidths=[col_full * 0.08, col_full * 0.62, col_full * 0.30])
            it.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), GREEN),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GREEN_L]),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(it)
            story.append(Spacer(1, 5 * mm))

        if exclusions:
            story.append(Paragraph("What's Not Included", s_section))
            exc_rows = [[
                Paragraph("<b>#</b>", s_white_b),
                Paragraph("<b>Exclusion</b>", s_white_b),
                Paragraph("<b>Category</b>", s_white_b),
            ]]
            for idx, ie in enumerate(exclusions, 1):
                exc_rows.append([
                    Paragraph(str(idx), s_body),
                    Paragraph(ie.incl_excl.item_service, s_body),
                    Paragraph(ie.incl_excl.category.name if ie.incl_excl.category else "", s_body_sm),
                ])
            et = Table(exc_rows, colWidths=[col_full * 0.08, col_full * 0.62, col_full * 0.30])
            et.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), RED),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, RED_L]),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(et)
            story.append(Spacer(1, 8 * mm))

        # ──────────────── TERMS & CONDITIONS ────────────────
        story.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceBefore=4, spaceAfter=8))
        story.append(Paragraph("Terms & Conditions", s_section))

        terms = [
            "This is a quotation and not a confirmation of booking. Booking is confirmed only upon receipt of the advance payment and written confirmation.",
            "All prices are per person and quoted in Indian Rupees (INR) unless stated otherwise. Prices are subject to change based on availability and currency fluctuations.",
            "A minimum advance of 50% of the total cost is required to confirm the booking. The balance must be paid at least 15 days before the date of travel.",
            "Standard hotel check-in time is 14:00 hrs and check-out time is 11:00 hrs. Early check-in and late check-out are subject to availability and may incur additional charges.",
            "The itinerary is subject to change due to weather conditions, local regulations, or unforeseen circumstances. The company reserves the right to alter, amend, or cancel any part of the itinerary.",
            "Cancellation charges apply as follows: 30+ days before departure — 25% of tour cost; 15–29 days — 50%; 7–14 days — 75%; Less than 7 days or no-show — 100%.",
            "Travel insurance is strongly recommended but not included unless explicitly mentioned. The company shall not be liable for any loss, injury, or damage during the tour.",
            "All disputes are subject to jurisdiction of the courts at the registered office of the company.",
            "By accepting this quotation, the guest agrees to the above terms and conditions.",
        ]
        for i, term in enumerate(terms, 1):
            story.append(Paragraph(f"<b>{i}.</b> {term}", s_terms))
            story.append(Spacer(1, 1.5 * mm))

        # ──────────────── FOOTER NOTE ────────────────
        story.append(Spacer(1, 8 * mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=6))
        story.append(Paragraph(
            "This itinerary has been prepared by <b>Tour Planner</b>. We hope you have a wonderful trip!",
            s_center,
        ))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            f"Generated on {plan.updated_at.strftime('%d %b %Y')} &nbsp;|&nbsp; Plan #{plan.plan_number}",
            S("foot", fontSize=7, textColor=LIGHT, alignment=TA_CENTER),
        ))

        # ── Build PDF ──
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=20 * mm, leftMargin=20 * mm,
            topMargin=18 * mm, bottomMargin=18 * mm,
        )
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