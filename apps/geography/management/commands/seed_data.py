"""
Management command: seed_data

Clears all non-superuser data and seeds from CSV files:
  - 01_countries.csv   → Country
  - 02_regions.csv     → Region
  - 03_attractions.csv → Attraction
  - 04_hotels.csv      → Hotel
  - 07_day_tours.csv   → DayTour

Usage:
    python manage.py seed_data
    python manage.py seed_data --yes   # skip confirmation prompt
"""

import csv
import re
import unicodedata
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.account.models import User
from apps.attractions.models import Attraction, AttractionImage
from apps.audit.models import AuditLog
from apps.day_tours.models import DayTour, DayTourAttraction
from apps.geography.models import Country, CountryImage, Region, RegionImage
from apps.hotel.models import Hotel, HotelImage
from apps.inclusions.models import InclExclCategory, InclusionExclusion
from apps.itinerary_templates.models import (
    ItineraryTemplate,
    ItineraryTemplateDay,
    ItineraryTemplateInclExcl,
)
from apps.user_plans.models import UserPlan, UserPlanDay, UserPlanInclExcl

# ─────────────────────────────────────────────
# CSV file paths (all relative to BASE_DIR)
# ─────────────────────────────────────────────
CSV_DIR = Path(settings.BASE_DIR)
COUNTRIES_CSV = CSV_DIR / "01_countries.csv"
REGIONS_CSV = CSV_DIR / "02_regions.csv"
ATTRACTIONS_CSV = CSV_DIR / "03_attractions.csv"
HOTELS_CSV = CSV_DIR / "04_hotels.csv"
INCLUSIONS_CSV = CSV_DIR / "05_inclusions_exclusions.csv"
DAY_TOURS_CSV = CSV_DIR / "07_day_tours.csv"


def _normalize(s: str) -> str:
    """Lowercase, strip, and remove accents for fuzzy region/country matching."""
    s = s.strip().lower()
    return unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("ASCII")


def _is_desc_row(row: dict) -> bool:
    """Return True if this row is the CSV description/instructions row (row 2).

    Each CSV has a second row where every cell contains text like
    'REQUIRED - ...', 'OPTIONAL - ...', or 'REQUIRED'.
    We detect this by checking whether any non-empty cell value in the row
    starts with 'REQUIRED' or 'OPTIONAL' (case-insensitive).
    """
    for val in row.values():
        v = val.strip().upper()
        if v.startswith("REQUIRED") or v.startswith("OPTIONAL"):
            return True
    return False


def _make_region_code(name: str) -> str:
    """Generate a ≤10-char uppercase code from a region name."""
    # Take alphanumeric chars only, uppercase, max 10
    clean = re.sub(r"[^A-Za-z0-9]", "", name.strip())
    return clean.upper()[:10] if clean else "REGION"


def _parse_star_rating(raw: str) -> int:
    """Extract integer from values like '5', '4-star', '3-star', etc."""
    raw = raw.strip()
    m = re.search(r"\d+", raw)
    if m:
        val = int(m.group())
        return max(1, min(5, val))  # clamp 1-5
    return 3  # default


class Command(BaseCommand):
    help = "Clear all data (keep superusers) and seed from CSV files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip confirmation prompt",
        )

    def handle(self, *args, **options):
        if not options["yes"]:
            self.stdout.write(
                self.style.WARNING(
                    "\nThis will DELETE all data (users, plans, tours, hotels, etc.)\n"
                    "Only superuser accounts (is_superuser=True) will be kept.\n"
                    "NOTE: Itinerary templates are cleared but NOT re-seeded.\n"
                )
            )
            confirm = input("Type 'yes' to continue: ").strip().lower()
            if confirm != "yes":
                self.stdout.write("Aborted.")
                return

        # Verify all CSV files exist before starting
        for csv_path in [COUNTRIES_CSV, REGIONS_CSV, ATTRACTIONS_CSV, HOTELS_CSV, INCLUSIONS_CSV, DAY_TOURS_CSV]:
            if not csv_path.exists():
                self.stderr.write(self.style.ERROR(f"CSV not found: {csv_path}"))
                return

        with transaction.atomic():
            self._clear_all_data()
            countries = self._seed_countries()
            regions = self._seed_regions(countries)
            self._seed_attractions(regions)
            self._seed_hotels(countries, regions)  # may auto-create missing regions
            self._seed_inclusions(countries)
            self._seed_day_tours(regions)

        self.stdout.write(self.style.SUCCESS("\n✓ Seeding complete!"))

    # ─────────────────────────────────────────
    # CLEAR
    # ─────────────────────────────────────────

    def _clear_all_data(self):
        self.stdout.write("\nClearing existing data...")

        # User plans (deepest FK first)
        count = UserPlanInclExcl.objects.all().delete()[0]
        count += UserPlanDay.objects.all().delete()[0]
        count += UserPlan.objects.all().delete()[0]

        # Itinerary templates
        ItineraryTemplateInclExcl.objects.all().delete()
        ItineraryTemplateDay.objects.all().delete()
        ItineraryTemplate.objects.all().delete()

        # Day tours
        DayTourAttraction.objects.all().delete()
        DayTour.objects.all().delete()

        # Hotels
        HotelImage.objects.all().delete()
        Hotel.objects.all().delete()

        # Attractions
        AttractionImage.objects.all().delete()
        Attraction.objects.all().delete()

        # Geography
        RegionImage.objects.all().delete()
        Region.objects.all().delete()
        CountryImage.objects.all().delete()
        Country.objects.all().delete()

        # Inclusions
        InclusionExclusion.objects.all().delete()
        InclExclCategory.objects.all().delete()

        # Audit logs
        AuditLog.objects.all().delete()

        # Non-superuser users
        deleted_users, _ = User.objects.filter(is_superuser=False).delete()
        kept = User.objects.filter(is_superuser=True).count()

        self.stdout.write(f"  Removed {deleted_users} non-superuser user(s). Kept {kept} superuser(s).")
        self.stdout.write("  All other data tables cleared.")

    # ─────────────────────────────────────────
    # COUNTRIES
    # ─────────────────────────────────────────

    def _seed_countries(self) -> dict:
        """Returns {code: Country} mapping."""
        self.stdout.write("\nSeeding countries...")
        countries = {}
        with open(COUNTRIES_CSV, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("name", "").strip()
                code = row.get("code", "").strip().upper()
                iso_code = row.get("iso_code", "").strip() or None

                # Skip the description row (row 2) and blank rows
                if not name or not code or _is_desc_row(row):
                    continue

                country = Country.objects.create(
                    name=name,
                    code=code,
                    iso_code=iso_code,
                    is_active=True,
                )
                countries[code] = country
                self.stdout.write(f"  + Country: {name} ({code})")

        self.stdout.write(f"  → {len(countries)} countries created.")
        return countries

    # ─────────────────────────────────────────
    # REGIONS
    # ─────────────────────────────────────────

    def _seed_regions(self, countries: dict) -> dict:
        """Returns {normalized_name: Region} mapping."""
        self.stdout.write("\nSeeding regions...")
        regions = {}
        used_codes = {}  # country_code → set of used region codes

        with open(REGIONS_CSV, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                country_code = row.get("country_code", "").strip().upper()
                name = row.get("name", "").strip()
                code = row.get("code", "").strip().upper()
                description = row.get("description", "").strip() or None
                display_order_raw = row.get("display_order", "0").strip()

                # Skip the description row (row 2) and blank rows
                if not name or not country_code or _is_desc_row(row):
                    continue

                country = countries.get(country_code)
                if not country:
                    self.stdout.write(
                        self.style.WARNING(f"  ! Region '{name}': unknown country code '{country_code}' — skipped")
                    )
                    continue

                # Auto-generate code if missing
                if not code:
                    base = _make_region_code(name)
                    code = base
                    existing = used_codes.setdefault(country_code, set())
                    suffix = 1
                    while code in existing:
                        code = f"{base[:8]}{suffix:02d}"
                        suffix += 1
                    used_codes[country_code].add(code)
                else:
                    used_codes.setdefault(country_code, set()).add(code)

                try:
                    display_order = int(display_order_raw)
                except ValueError:
                    display_order = 0

                region = Region.objects.create(
                    country=country,
                    name=name,
                    code=code,
                    description=description,
                    display_order=display_order,
                    is_active=True,
                )
                key = _normalize(name)
                regions[key] = region
                self.stdout.write(f"  + Region: {name} [{code}] ({country_code})")

        self.stdout.write(f"  → {len(regions)} regions created.")
        return regions

    # ─────────────────────────────────────────
    # ATTRACTIONS
    # ─────────────────────────────────────────

    def _seed_attractions(self, regions: dict):
        self.stdout.write("\nSeeding attractions...")
        created = 0
        skipped = 0

        with open(ATTRACTIONS_CSV, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                region_raw = row.get("region", "").strip()
                name = row.get("name", "").strip()
                key_features = row.get("key_features_notes", "").strip() or None
                source_citations = row.get("source_citations", "").strip() or None
                lat_raw = row.get("latitude", "").strip()
                lng_raw = row.get("longitude", "").strip()
                display_order_raw = row.get("display_order", "0").strip()

                if not name or not region_raw or _is_desc_row(row):
                    continue

                region = regions.get(_normalize(region_raw))
                if not region:
                    self.stdout.write(
                        self.style.WARNING(f"  ! Attraction '{name}': region '{region_raw}' not found — skipped")
                    )
                    skipped += 1
                    continue

                try:
                    lat = float(lat_raw) if lat_raw else None
                except ValueError:
                    lat = None
                try:
                    lng = float(lng_raw) if lng_raw else None
                except ValueError:
                    lng = None
                try:
                    display_order = int(display_order_raw)
                except ValueError:
                    display_order = 0

                # Generate unique reference_no: ATT-{REGION_CODE}-{seq:03d}
                reference_no = f"ATT-{region.code}-{i+1:03d}"
                # Ensure uniqueness (handle rare collisions)
                suffix = 1
                base_ref = reference_no
                while Attraction.objects.filter(reference_no=reference_no).exists():
                    reference_no = f"{base_ref[:16]}-{suffix}"
                    suffix += 1

                Attraction.objects.create(
                    region=region,
                    reference_no=reference_no,
                    name=name,
                    key_features_notes=key_features,
                    source_citations=source_citations,
                    latitude=lat,
                    longitude=lng,
                    display_order=display_order,
                    is_active=True,
                )
                created += 1
                self.stdout.write(f"  + Attraction: {name} [{reference_no}]")

        self.stdout.write(f"  → {created} attractions created, {skipped} skipped.")

    # ─────────────────────────────────────────
    # HOTELS
    # ─────────────────────────────────────────

    def _seed_hotels(self, countries: dict, regions: dict):
        self.stdout.write("\nSeeding hotels...")
        created = 0
        skipped = 0

        with open(HOTELS_CSV, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                country_code = row.get("country_code", "").strip().upper()
                region_raw = row.get("region", "").strip()
                name = row.get("name", "").strip()
                city = row.get("city", "").strip() or None
                address = row.get("address", "").strip() or None
                star_rating_raw = row.get("star_rating", "3").strip()
                hotel_type = row.get("hotel_type", "").strip() or None
                description = row.get("description", "").strip() or None
                contact_phone = row.get("contact_phone", "").strip() or None
                contact_email = row.get("contact_email", "").strip() or None
                website = row.get("website", "").strip() or None
                check_in_time = row.get("check_in_time", "").strip() or None
                check_out_time = row.get("check_out_time", "").strip() or None
                lat_raw = row.get("latitude", "").strip()
                lng_raw = row.get("longitude", "").strip()
                amenities_raw = row.get("amenities", "").strip() or None
                price_raw = row.get("price_notes", "").strip()  # e.g. "ISK 40000" or "From CHF 450/night"
                display_order_raw = row.get("display_order", "0").strip()

                if not name or not country_code or _is_desc_row(row):
                    continue

                country = countries.get(country_code)
                if not country:
                    self.stdout.write(
                        self.style.WARNING(f"  ! Hotel '{name}': unknown country '{country_code}' — skipped")
                    )
                    skipped += 1
                    continue

                region = regions.get(_normalize(region_raw))
                if not region:
                    # Auto-create the region rather than skipping the hotel
                    auto_code = _make_region_code(region_raw)
                    # Ensure code is unique within this country
                    existing_codes = set(
                        Region.objects.filter(country=country).values_list("code", flat=True)
                    )
                    suffix = 1
                    final_code = auto_code
                    while final_code in existing_codes:
                        final_code = f"{auto_code[:8]}{suffix:02d}"
                        suffix += 1
                    region = Region.objects.create(
                        country=country,
                        name=region_raw.strip(),
                        code=final_code,
                        is_active=True,
                    )
                    regions[_normalize(region_raw)] = region
                    self.stdout.write(
                        self.style.NOTICE(f"  ~ Auto-created region '{region_raw}' [{final_code}] for hotel '{name}'")
                    )

                star_rating = _parse_star_rating(star_rating_raw) if star_rating_raw else 3

                try:
                    lat = float(lat_raw) if lat_raw else None
                except ValueError:
                    lat = None
                try:
                    lng = float(lng_raw) if lng_raw else None
                except ValueError:
                    lng = None
                try:
                    display_order = int(display_order_raw)
                except ValueError:
                    display_order = 0

                # Parse amenities: comma-separated string → list
                amenities = None
                if amenities_raw:
                    amenities = [a.strip() for a in amenities_raw.split(",") if a.strip()]

                # Parse price from price_notes column (e.g. "ISK 40000", "From CHF 450/night")
                VALID_CURRENCIES = {"INR", "USD", "EUR", "ISK", "CHF"}
                price_currency = "INR"
                price_per_night = None
                if price_raw:
                    # Try to extract a known currency code from the string
                    for cur in VALID_CURRENCIES:
                        if cur in price_raw.upper():
                            price_currency = cur
                            break
                    # Extract the first numeric value (may be float)
                    num_match = re.search(r"[\d]+(?:[.,]\d+)?", price_raw.replace(",", ""))
                    if num_match:
                        try:
                            price_per_night = float(num_match.group())
                        except ValueError:
                            price_per_night = None

                Hotel.objects.create(
                    name=name,
                    country=country,
                    region=region,
                    city=city,
                    address=address,
                    star_rating=star_rating,
                    hotel_type=hotel_type,
                    description=description,
                    contact_phone=contact_phone,
                    contact_email=contact_email,
                    website=website,
                    check_in_time=check_in_time,
                    check_out_time=check_out_time,
                    latitude=lat,
                    longitude=lng,
                    amenities=amenities,
                    price_per_night=price_per_night or 0,
                    price_currency=price_currency,
                    price_notes=price_raw or None,
                    display_order=display_order,
                    is_active=True,
                )
                created += 1
                self.stdout.write(f"  + Hotel: {name} ({region_raw})")

        self.stdout.write(f"  → {created} hotels created, {skipped} skipped.")

    # ─────────────────────────────────────────
    # DAY TOURS
    # ─────────────────────────────────────────

    # ─────────────────────────────────────────
    # INCLUSIONS / EXCLUSIONS
    # ─────────────────────────────────────────

    def _seed_inclusions(self, countries: dict):
        self.stdout.write("\nSeeding inclusions/exclusions...")
        created = 0
        skipped = 0

        # Build category map (auto-create)
        cat_map = {c.name.strip().lower(): c for c in InclExclCategory.objects.all()}
        existing_codes = set(InclusionExclusion.objects.values_list("unique_code", flat=True))

        with open(INCLUSIONS_CSV, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if _is_desc_row(row):
                    continue

                country_code = row.get("country_code", "").strip().upper()
                unique_code = row.get("unique_code", "").strip()
                type_val = row.get("type", "").strip().upper()
                category_name = row.get("category", "").strip()
                item_service = row.get("item_service", "").strip()
                details_notes = row.get("details_notes", "").strip() or None
                source_files = row.get("source_files", "").strip() or None
                display_order_raw = row.get("display_order", "0").strip()

                if not item_service or not unique_code:
                    continue

                if type_val not in ("INCLUSION", "EXCLUSION"):
                    self.stdout.write(self.style.WARNING(f"  ! '{unique_code}': invalid type '{type_val}' — skipped"))
                    skipped += 1
                    continue

                country = countries.get(country_code)
                if not country:
                    self.stdout.write(self.style.WARNING(f"  ! '{unique_code}': unknown country '{country_code}' — skipped"))
                    skipped += 1
                    continue

                if unique_code in existing_codes:
                    skipped += 1
                    continue

                if not category_name:
                    skipped += 1
                    continue

                cat_key = category_name.lower()
                if cat_key not in cat_map:
                    cat_obj = InclExclCategory.objects.create(name=category_name, is_active=True)
                    cat_map[cat_key] = cat_obj
                    self.stdout.write(f"  ~ Category created: {category_name}")
                category = cat_map[cat_key]

                try:
                    display_order = int(display_order_raw)
                except ValueError:
                    display_order = 0

                InclusionExclusion.objects.create(
                    country=country,
                    unique_code=unique_code,
                    type=type_val,
                    category=category,
                    item_service=item_service,
                    details_notes=details_notes,
                    source_files=source_files,
                    display_order=display_order,
                    is_active=True,
                )
                existing_codes.add(unique_code)
                created += 1
                self.stdout.write(f"  + [{type_val}] {item_service} ({country_code})")

        self.stdout.write(f"  → {created} inclusion/exclusion items created, {skipped} skipped.")

    def _seed_day_tours(self, regions: dict):
        self.stdout.write("\nSeeding day tours...")
        created = 0
        skipped = 0

        with open(DAY_TOURS_CSV, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                region_raw = row.get("region", "").strip()
                validity_mode = row.get("validity_mode", "OPEN").strip().upper() or "OPEN"
                valid_from_raw = row.get("valid_from", "").strip() or None
                valid_to_raw = row.get("valid_to", "").strip() or None
                price_raw = row.get("price", "").strip()
                currency = row.get("currency", "INR").strip().upper() or "INR"
                activity_combination = row.get("activity_combination", "").strip()
                est_time_distance = row.get("est_time_distance", "").strip() or None
                overnight_location = row.get("overnight_location", "").strip() or None
                source_file = row.get("source_file", "").strip() or None
                itinerary_text = row.get("itinerary_text", "").strip()
                display_order_raw = row.get("display_order", "0").strip()

                # Skip the description row (row 2) and blank rows
                if not activity_combination or not region_raw or _is_desc_row(row):
                    continue

                region = regions.get(_normalize(region_raw))
                if not region:
                    self.stdout.write(
                        self.style.WARNING(f"  ! Day tour '{activity_combination[:50]}': region '{region_raw}' not found — skipped")
                    )
                    skipped += 1
                    continue

                # Validate validity_mode against choices
                valid_modes = {"OPEN", "DATE_RANGE", "MONTH", "YEAR"}
                if validity_mode not in valid_modes:
                    validity_mode = "OPEN"

                # Validate against CurrencyType choices: INR, USD, EUR, ISK, CHF
                # Any unrecognised value falls back to INR
                if currency not in {"INR", "USD", "EUR", "ISK", "CHF"}:
                    currency = "INR"

                try:
                    price = float(price_raw) if price_raw else None
                except ValueError:
                    price = None

                try:
                    display_order = int(display_order_raw)
                except ValueError:
                    display_order = 0

                # Generate unique_code: DT-{REGION_CODE}-{seq:03d}
                unique_code = f"DT-{region.code}-{i+1:03d}"
                suffix = 1
                base_code = unique_code
                while DayTour.objects.filter(unique_code=unique_code).exists():
                    unique_code = f"{base_code[:16]}-{suffix}"
                    suffix += 1

                # If itinerary_text is empty, fall back to activity_combination
                if not itinerary_text:
                    itinerary_text = activity_combination

                DayTour.objects.create(
                    region=region,
                    unique_code=unique_code,
                    validity_mode=validity_mode,
                    valid_from=valid_from_raw or None,
                    valid_to=valid_to_raw or None,
                    price=price,
                    currency=currency,
                    activity_combination=activity_combination,
                    est_time_distance=est_time_distance,
                    overnight_location=overnight_location,
                    source_file=source_file,
                    itinerary_text=itinerary_text,
                    display_order=display_order,
                    is_active=True,
                )
                created += 1
                self.stdout.write(f"  + Day Tour: {activity_combination[:60]}...")

        self.stdout.write(f"  → {created} day tours created, {skipped} skipped.")
