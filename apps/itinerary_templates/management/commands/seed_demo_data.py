"""
Management command: seed_demo_data

Clears and re-seeds Switzerland and Iceland with:
  - 20 regions each
  - 1-2 day tours per region (realistic activity descriptions)
  - 2 ItineraryTemplates per region (one Day-only, one Day+Night) with is_default=True on one
  - 10 inclusions + 10 exclusions per country across categories

Usage:
    python manage.py seed_demo_data
    python manage.py seed_demo_data --clear   # wipe all seeded data first
"""

import secrets
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from apps.geography.models import Country, Region
from apps.inclusions.models import InclExclCategory, InclusionExclusion
from apps.attractions.models import Attraction
from apps.day_tours.models import DayTour, DayTourAttraction
from apps.itinerary_templates.models import (
    ItineraryTemplate, ItineraryTemplateDay, ItineraryTemplateInclExcl
)
from apps.account.models import User

# ──────────────────────────────────────────────────────────────────────────────
# DATA DEFINITIONS
# ──────────────────────────────────────────────────────────────────────────────

SWITZERLAND_REGIONS = [
    ("ZUR", "Zurich & Surroundings",
     "Switzerland's largest city, famous for the old town, Lake Zurich, and world-class museums."),
    ("LUC", "Lucerne & Central Switzerland",
     "Picturesque lakeside city with the iconic Chapel Bridge, surrounded by mountains."),
    ("BER", "Bern & Bernese Oberland",
     "The Swiss capital with a UNESCO-listed old town and easy access to Jungfrau region."),
    ("INT", "Interlaken & Jungfrau",
     "Adventure Hub between Thun and Brienz lakes, gateway to Jungfraujoch – Top of Europe."),
    ("GEN", "Geneva & Lake Geneva",
     "International city with the Jet d'Eau, UN headquarters, and stunning lakefront."),
    ("LAU", "Lausanne & Western Switzerland",
     "Home of the Olympic Museum, terraced vineyards of Lavaux, and French-Swiss culture."),
    ("ZER", "Zermatt & Matterhorn",
     "Car-free alpine village beneath the iconic Matterhorn peak."),
    ("STG", "St. Gallen & Eastern Switzerland",
     "Baroque abbey library, Rhine Falls nearby, and traditional Appenzell countryside."),
    ("CUR", "Davos & Graubünden",
     "High-altitude resort city known for the World Economic Forum and world-class skiing."),
    ("MON", "Montreux & Swiss Riviera",
     "Famous for the Jazz Festival, Chillon Castle, and subtropical microclimate on Lake Geneva."),
    ("BAS", "Basel & Rhine",
     "Cultural capital hosting Art Basel, world-class museums, and the Rhine river promenade."),
    ("ANZ", "Andermatt & Uri Alps",
     "Alpine crossroads with the Gotthard Pass, Schöllenen Gorge, and pristine ski terrain."),
    ("MEI", "Meiringen & Bernese Highlands",
     "Gateway to the Aare Gorge, Rosenlauigletscher, and Sherlock Holmes Museum."),
    ("SAA", "Saas-Fee & Valais",
     "Glacier village offering year-round skiing at 3,500m with stunning 4,000m peaks."),
    ("LOC", "Locarno & Ticino",
     "Italian-speaking Swiss canton with palm trees, lakes, and the Piazza Grande film festival."),
    ("LUG", "Lugano & Southern Ticino",
     "Mediterranean flair meets alpine scenery, with Monte Brè, Monte San Salvatore, and luxury shopping."),
    ("GRI", "Grindelwald & Bernese Alps",
     "Alpine village beneath the Eiger North Face; base for hiking, skiing, and FIRST cliff walk."),
    ("SOL", "Solothurn & Mittelland",
     "Baroque city of ambassadors; St. Ursus Cathedral, 11 fountains, 11 towers and a laid-back charm."),
    ("FRI", "Fribourg & Sense",
     "Bilingual medieval city with a preserved Gothic old town, Gottéron gorge, and fondue culture."),
    ("ENG", "Engadin Valley & St. Moritz",
     "1,800m high valley with turquoise lakes, St. Moritz glamour, and the Glacier Express route."),
]

ICELAND_REGIONS = [
    ("REY", "Reykjavik & Capital Region",
     "Iceland's vibrant capital with colorful houses, geothermal pools, world-class restaurants, and Saturday night culture."),
    ("SNA", "Snæfellsnes Peninsula",
     "Jules Verne's gateway to the Earth's centre; Snæfellsjökull glacier, Kirkjufell mountain, and dramatic lava fields."),
    ("WFJ", "West Fjords",
     "Iceland's most remote region; towering sea cliffs at Látrabjarg, Arctic foxes, and mirror-calm fjords."),
    ("NOR", "North Iceland & Akureyri",
     "Whale watching capital, dramatic Goðafoss waterfall, and the whale museum of Husavík."),
    ("DIA", "Diamond Circle — Lake Mývatn",
     "Geothermal wonderland with pseudo-craters, Dimmuborgir lava formations, and bubbling mud pools."),
    ("EAS", "East Iceland & Eastfjords",
     "Rugged fjord scenery, reindeer herds, seabird cliffs, and the Vatnajökull glacier lagoon area."),
    ("GCR", "Golden Circle",
     "Iceland's most famous route: Þingvellir National Park, Geysir, and Gullfoss waterfall."),
    ("SOU", "South Coast",
     "Black sand beaches of Reynisfjara, Seljalandsfoss, Skógafoss, and Eyjafjallajökull glacier."),
    ("VAT", "Vatnajökull Glacier & Jökulsárlón",
     "Europe's largest glacier with ice caves, the Diamond Beach iceberg lagoon, and Skaftafell hiking."),
    ("VES", "Vestmannaeyjar — Westman Islands",
     "Volcanic archipelago; Eldfell volcano, world's largest puffin colony, and thrilling ferry crossing."),
    ("LAK", "Lakagígar & Highland Interior",
     "Remote lava field system from the 1783 Laki eruption; F-road adventure territory, accessible Jun–Sep only."),
    ("KER", "Kerlingarfjöll & Hot Springs",
     "Highland geothermal wonderland with rhyolite mountains, hot rivers, and natural hot tubs."),
    ("HEK", "Hekla & Southern Highlands",
     "Active volcano zone with lava tubes, geysers, and access to Landmannalaugar rainbow mountains."),
    ("AUR", "Aurora Trail — North & Northeast",
     "Best dark-sky zone for Northern Lights; remote farms, horse breeding valley, and rural Icelandic culture."),
    ("PEN", "Reykjanes Peninsula & Blue Lagoon",
     "UNESCO-listed geothermal landscape with the famous Blue Lagoon, Bridge Between Continents, and lava fields."),
    ("THO", "Þórsmörk — Thor's Valley",
     "Glacial valley between three glaciers; Fimmvörðuháls trek, Stakkholtsgjá canyon, and highland wildlife."),
    ("HOL", "Hólmavík & Strandir Coast",
     "Far West Fjords experience with the Museum of Icelandic Sorcery, deserted coastlines, and seal watching."),
    ("ASB", "Askja & Highlands Caldera",
     "Remote volcanic caldera with Viti crater lake, accessible only via highland F-roads in summer."),
    ("GRI", "Grímsey Island & Arctic Circle",
     "The only Icelandic territory north of the Arctic Circle; puffins, cliff hiking, and midnight sun fishing."),
    ("HUS", "Húsavík & Whale Capital",
     "World capital of whale watching; humpback whales, whale museum, and thrilling sea adventures."),
]

INCLUSIONS = {
    "Transport": [
        ("Airport transfers in private vehicle", "INCLUSION"),
        ("All inter-city transfers as per itinerary", "INCLUSION"),
        ("Private coach transportation throughout", "INCLUSION"),
    ],
    "Accommodation": [
        ("4-star hotel accommodation with breakfast", "INCLUSION"),
        ("Boutique hotel stay in city centres", "INCLUSION"),
    ],
    "Meals": [
        ("Daily breakfast included", "INCLUSION"),
        ("Welcome dinner on Day 1", "INCLUSION"),
        ("Farewell dinner at local restaurant", "INCLUSION"),
    ],
    "Activities": [
        ("All entrance fees as per itinerary", "INCLUSION"),
        ("Guided city walking tour", "INCLUSION"),
        ("Boat/cable car tickets as mentioned", "INCLUSION"),
    ],
    "Extras": [
        ("Dedicated English-speaking tour guide", "INCLUSION"),
        ("24/7 helpline support", "INCLUSION"),
        ("Comprehensive travel insurance", "INCLUSION"),
    ],
}

EXCLUSIONS = {
    "Personal": [
        ("Personal expenses and shopping", "EXCLUSION"),
        ("Tips and gratuities for guides/drivers", "EXCLUSION"),
        ("Camera/video fees at monuments", "EXCLUSION"),
    ],
    "Meals": [
        ("Lunches and dinners (unless specified)", "EXCLUSION"),
        ("Alcoholic beverages and soft drinks", "EXCLUSION"),
        ("Room service charges", "EXCLUSION"),
    ],
    "Travel": [
        ("International airfare", "EXCLUSION"),
        ("Visa fees and processing charges", "EXCLUSION"),
        ("Travel insurance (if not opted)", "EXCLUSION"),
    ],
    "Optional": [
        ("Optional excursions not in the itinerary", "EXCLUSION"),
        ("Gondola/hot-air balloon rides", "EXCLUSION"),
        ("Spa and wellness services", "EXCLUSION"),
    ],
}

# Day tour templates per region — one realistic activity per region
CH_TOURS = {
    "ZUR": ("ZUR Zurich City & Lake Tour",
            "Old Town • Lake Zurich Cruise • Swiss National Museum • Bahnhofstrasse",
            "Full day — approx 8 hrs | 15 km walking+boat"),
    "LUC": ("LUC Lucerne Highlights & Lake Cruise",
            "Chapel Bridge • Lion Monument • Lake Lucerne Panorama Cruise • Glacier Garden",
            "Full day — approx 7 hrs"),
    "BER": ("BER Bern Old Town & Rose Garden",
            "Federal Palace • Bear Park • Zytglogge • Rose Garden Viewpoint",
            "Full day — approx 7 hrs"),
    "INT": ("INT Jungfraujoch — Top of Europe",
            "Jungfraujoch 3,454m • Aletsch Glacier Viewpoint • Ice Palace • Sphinx Observatory",
            "Full day — approx 9 hrs | Return train included"),
    "GEN": ("GEN Geneva City Tour & Jet d'Eau",
            "Jet d'Eau • Old Town • Palais des Nations Garden • Flower Clock • Lake Promenade",
            "Full day — approx 7 hrs"),
    "LAU": ("LAU Lavaux Vineyards UNESCO Walk",
            "Cully Village Walk • Lavaux Terraced Vineyards • Puidoux Viewpoint • Local Wine Tasting",
            "Half day — approx 5 hrs"),
    "ZER": ("ZER Matterhorn & Glacier Paradise",
            "Matterhorn Glacier Paradise 3,883m • Ice Palace • Mountain View Terrace • Zermatt Village Walk",
            "Full day — approx 9 hrs"),
    "STG": ("STG Rhine Falls & St. Gallen Abbey",
            "Rhine Falls • St. Gallen Abbey Library (UNESCO) • Old Town Oriel Windows Walk",
            "Full day — approx 8 hrs"),
    "CUR": ("CUR Davos & Schatzalp Forest Trail",
            "Schatzalp Botanical Garden • Davos Lake Walk • Seehorn Circular Hike",
            "Full day — approx 7 hrs"),
    "MON": ("MON Montreux & Chillon Castle",
            "Château de Chillon • Montreux Promenade • Queen Studio Experience • Lake Geneva Cruise",
            "Full day — approx 8 hrs"),
    "BAS": ("BAS Basel Museum Quarter & Rhine",
            "Kunstmuseum Basel • Mittlere Rheinbrücke Walk • Basel Minster • Rhine Riverbank",
            "Full day — approx 7 hrs"),
    "ANZ": ("ANZ Andermatt & Teufelsbrücke",
            "Devil's Bridge • Schöllenen Gorge • Gotthard Pass Museum • Andermatt Village",
            "Full day — approx 8 hrs"),
    "MEI": ("MEI Aare Gorge & Reichenbach Falls",
            "Aare Gorge Walk • Reichenbach Falls (Sherlock Holmes) • Meiringen Village",
            "Half day — approx 5 hrs"),
    "SAA": ("SAA Saas-Fee Allalin Glacier",
            "Metro Alpin to 3,500m • Allalin Glacier Walk • Ice Pavilion • Saas-Fee Village",
            "Full day — approx 9 hrs"),
    "LOC": ("LOC Locarno & Cardada Mountain",
            "Cardada Cimetta Cable Car • Piazza Grande • Madonna del Sasso Sanctuary • Lake Maggiore",
            "Full day — approx 7 hrs"),
    "LUG": ("LUG Lugano City & Monte Brè",
            "Monte Brè Funicular • Lugano Old Town • Parco Ciani Walk • Lugano Lake Boat Tour",
            "Full day — approx 8 hrs"),
    "GRI": ("GRI Grindelwald FIRST Cliff Walk",
            "FIRST Cliff Walk by Tissot • FIRST Flyer • Bachalpsee Hike • Eiger North Face Viewpoint",
            "Full day — approx 9 hrs"),
    "SOL": ("SOL Solothurn Baroque City Walk",
            "St. Ursus Cathedral • Old Armory • 11 Towers Walk • Aare Riverside Promenade",
            "Half day — approx 4 hrs"),
    "FRI": ("FRI Fribourg Old Town & Gottéron",
            "Gottéron Gorge Walk • St. Nicolas Cathedral • Bern Gate • Chocolate Factory Visit",
            "Full day — approx 7 hrs"),
    "ENG": ("ENG Engadin Lake & St. Moritz Glam",
            "St. Moritz Village • Engadin Lake Walk • Maloja Pass • Sils Maria Village",
            "Full day — approx 8 hrs"),
}

IS_TOURS = {
    "REY": ("REY Reykjavik City & Hallgrímskirkja",
            "Hallgrímskirkja Church • Harpa Concert Hall • Sun Voyager Sculpture • Old Harbour Walk",
            "Full day — approx 7 hrs"),
    "SNA": ("SNA Snæfellsnes & Kirkjufell",
            "Kirkjufell Mountain • Djúpalónssandur Beach • Arnarstapi Cliffs • Snæfellsjökull Glacier",
            "Full day — approx 10 hrs"),
    "WFJ": ("WFJ Látrabjarg Bird Cliffs",
            "Látrabjarg Puffin Cliffs • Rauðisandur Beach • Dynjandi Waterfall • Remote Fjord Drive",
            "Full day — approx 12 hrs"),
    "NOR": ("NOR Goðafoss & Whale Watching",
            "Goðafoss Waterfall • Akureyri Botanic Garden • Whale Watching Boat Tour",
            "Full day — approx 9 hrs"),
    "DIA": ("DIA Mývatn Nature Baths",
            "Mývatn Nature Baths • Dimmuborgir Lava Fields • Grjótagjá Cave • Krafla Caldera",
            "Full day — approx 10 hrs"),
    "EAS": ("EAS Eastfjords Scenic Drive",
            "Djúpivogur Village • Petra's Stone Collection • Stóðvarfjörður • Reyðarfjörður",
            "Full day — approx 10 hrs"),
    "GCR": ("GCR Golden Circle Full Day",
            "Þingvellir National Park • Strokkur Geysir • Gullfoss Waterfall • Þrídrangar View",
            "Full day — approx 10 hrs"),
    "SOU": ("SOU South Coast Waterfalls",
            "Seljalandsfoss • Gljúfrabúi Hidden Waterfall • Skógafoss • Reynisfjara Black Beach",
            "Full day — approx 10 hrs"),
    "VAT": ("VAT Jökulsárlón Glacier Lagoon",
            "Jökulsárlón Glacier Lagoon Boat Tour • Diamond Beach • Skaftafell Svartifoss Hike",
            "Full day — approx 10 hrs"),
    "VES": ("VES Westman Islands Ferry Tour",
            "Ferry from Landeyjahöfn • Eldfell Volcano Hike • Lava Fields Walk • Puffin Coastal Walk",
            "Full day — approx 9 hrs"),
    "LAK": ("LAK Lakagígar Lava System",
            "F206 Highland Route • Laki Crater Row • Tjarnargígur Lava Lake • Eldgjá Gorge",
            "Full day — approx 11 hrs | F-road 4WD vehicle required"),
    "KER": ("KER Kerlingarfjöll Hot Springs Trek",
            "Kerlingarfjöll Geothermal Trek • Hveradalir Hot Springs • Rhyolite Mountain Views",
            "Full day — approx 9 hrs"),
    "HEK": ("HEK Landmannalaugar Rainbow Mountains",
            "Landmannalaugar Geothermal Pool • Rainbow Mountains Hike • Laugahraun Lava Field",
            "Full day — approx 11 hrs"),
    "AUR": ("AUR Northern Lights & Dark Sky Tour",
            "Rural Dark Sky Zone Drive • Aurora Borealis Hunt • Village of Varmahlíð • Glaumbaer Turf Farm",
            "Evening tour — 6 hrs | Best Oct–Mar"),
    "PEN": ("PEN Blue Lagoon & Reykjanes",
            "Blue Lagoon Geothermal Spa • Bridge Between Continents • Gunnuhver Hot Springs • Reykjanes Lighthouse",
            "Full day — approx 8 hrs"),
    "THO": ("THO Þórsmörk Valley Trek",
            "Þórsmörk Glacier Valley • Stakkholtsgjá Canyon Hike • Fimmvörðuháls Trail Start",
            "Full day — approx 10 hrs | Super jeep required"),
    "HOL": ("HOL Strandir Seal Watching",
            "Djúpavík • Sorcery Museum Hólmavík • Seal Colony Coastline • Bjarnarfjörður Fjord",
            "Full day — approx 10 hrs"),
    "ASB": ("ASB Askja Caldera & Viti Crater",
            "F88 Highland Route • Askja Caldera • Viti Crater Lake Swim • Öskjuvatn Lake",
            "Full day — approx 12 hrs | F-road required Jul–Sep"),
    "GRI": ("GRI Arctic Circle Grímsey",
            "Grímsey Island Flight & Crossing Arctic Circle • Puffin Cliff Walk • Midnight Sun Experience",
            "Full day — approx 9 hrs | Season: May–Aug"),
    "HUS": ("HUS Húsavík Whale Watching",
            "RIB Whale Watching Boat from Húsavík • Whale Museum • Geosea Geothermal Sea Baths",
            "Full day — approx 8 hrs"),
}


def _code():
    return "IT-" + str(secrets.randbelow(900000) + 100000)


def _dt_code(prefix):
    return f"DT-{prefix}-{secrets.randbelow(9000) + 1000}"


def _ie_code(prefix):
    return f"IE-{prefix}-{secrets.randbelow(9000) + 1000}"


class Command(BaseCommand):
    help = "Seed Switzerland & Iceland demo data (countries, regions, day tours, templates, inclusions)"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Clear all seeded data before re-seeding")

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear()

        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stderr.write("No superuser found. Create one first with: python manage.py createsuperuser")
            return

        with transaction.atomic():
            ch = self._seed_country("Switzerland", "CHE", "CHE")
            is_ = self._seed_country("Iceland", "ISL", "ISL")

            cats = self._seed_categories()
            ch_incl, ch_excl = self._seed_inclusions(ch, cats)
            is_incl, is_excl = self._seed_inclusions(is_, cats)

            self._seed_regions_and_templates(ch, SWITZERLAND_REGIONS, CH_TOURS, admin, ch_incl, ch_excl)
            self._seed_regions_and_templates(is_, ICELAND_REGIONS, IS_TOURS, admin, is_incl, is_excl)

        self.stdout.write(self.style.SUCCESS(
            "\n- Seeded: Switzerland + Iceland | 20 regions each | 40 day tours | 80 templates | inclusions & exclusions\n"
        ))
    def _clear(self):
        self.stdout.write("  Clearing old seeded data ...")
        for code in ("CHE", "ISL"):
            country_qs = Country.objects.filter(code=code)
            if not country_qs.exists():
                continue
            country = country_qs.first()
            # Delete in dependency order to avoid ProtectedError
            template_ids = ItineraryTemplate.objects.filter(country=country).values_list('id', flat=True)
            ItineraryTemplateInclExcl.objects.filter(template_id__in=template_ids).delete()
            ItineraryTemplateDay.objects.filter(template_id__in=template_ids).delete()
            ItineraryTemplate.objects.filter(country=country).delete()
            InclusionExclusion.objects.filter(country=country).delete()
            # DayTours and Attractions are region-scoped
            region_ids = Region.objects.filter(country=country).values_list('id', flat=True)
            DayTourAttraction.objects.filter(day_tour__region_id__in=region_ids).delete()
            DayTour.objects.filter(region_id__in=region_ids).delete()
            Attraction.objects.filter(region_id__in=region_ids).delete()
            Region.objects.filter(country=country).delete()
            country_qs.delete()
        self.stdout.write("  Done.")

    def _seed_country(self, name, code, iso):
        country, created = Country.objects.get_or_create(
            code=code,
            defaults={"name": name, "iso_code": iso, "is_active": True}
        )
        action = "Created" if created else "Found"
        self.stdout.write(f"  {action} country: {name}")
        return country

    def _seed_categories(self):
        cats = {}
        for name in list(INCLUSIONS.keys()) + [k for k in EXCLUSIONS if k not in INCLUSIONS]:
            cat, _ = InclExclCategory.objects.get_or_create(name=name, defaults={"is_active": True})
            cats[name] = cat
        return cats

    def _seed_inclusions(self, country, cats):
        incl_objs, excl_objs = [], []
        for cat_name, items in INCLUSIONS.items():
            cat = cats[cat_name]
            for item_text, itype in items:
                ie, _ = InclusionExclusion.objects.get_or_create(
                    country=country,
                    item_service=item_text,
                    defaults={
                        "unique_code": _ie_code(country.code),
                        "type": itype,
                        "category": cat,
                        "is_active": True,
                    }
                )
                incl_objs.append(ie)
        for cat_name, items in EXCLUSIONS.items():
            cat, _ = InclExclCategory.objects.get_or_create(name=cat_name, defaults={"is_active": True})
            for item_text, itype in items:
                ie, _ = InclusionExclusion.objects.get_or_create(
                    country=country,
                    item_service=item_text,
                    defaults={
                        "unique_code": _ie_code(country.code),
                        "type": itype,
                        "category": cat,
                        "is_active": True,
                    }
                )
                excl_objs.append(ie)
        self.stdout.write(f"  Inclusions/Exclusions for {country.name}: {len(incl_objs)} incl, {len(excl_objs)} excl")
        return incl_objs, excl_objs

    def _seed_regions_and_templates(self, country, regions_data, tours_data, admin, incl_list, excl_list):
        for i, (code, name, desc) in enumerate(regions_data):
            # Region — use country prefix to avoid cross-country code collision
            region_code = f"{country.code[:2]}{code}"[:10]
            region, _ = Region.objects.get_or_create(
                country=country,
                name=name,
                defaults={"code": region_code, "description": desc, "display_order": i + 1, "is_active": True}
            )

            # Day Tour (1 per region) — use raw SQL to handle legacy NOT NULL columns
            tour_data = tours_data.get(code)
            if tour_data:
                tour_name, activity, timing = tour_data
                day_tour = self._get_or_create_day_tour(
                    region=region,
                    activity_combination=activity,
                    unique_code=_dt_code(code),
                    itinerary_text=(
                        f"{timing}\n\nExplore {name} on this immersive day tour. "
                        f"Your expert guide will take you through the highlights, "
                        f"sharing local stories and insider tips throughout the day."
                    ),
                    est_time_distance=timing.split("\n")[0],
                )
                
                # Parse activity string into distinct Attractions
                attractions_list = [a.strip() for a in activity.split("•") if a.strip()]
                for idx, attr_name in enumerate(attractions_list):
                    attraction, _ = Attraction.objects.get_or_create(
                        region=region,
                        name=attr_name[:200],
                        defaults={
                            "reference_no": f"ATT-{region.code}-{idx+1}-{secrets.randbelow(9000)+1000}",
                            "key_features_notes": f"A major highlight of {name}.",
                            "is_active": True
                        }
                    )
                    DayTourAttraction.objects.get_or_create(
                        day_tour=day_tour,
                        attraction=attraction,
                        defaults={"visit_order": idx + 1}
                    )
                    
            else:
                day_tour = self._get_or_create_day_tour(
                    region=region,
                    activity_combination=f"{name} Highlights Tour",
                    unique_code=_dt_code(code),
                    itinerary_text=f"Explore the highlights of {name} with a local guide.",
                    est_time_distance="",
                )

            # Template 1: Day-only (is_default=True)
            tmpl1_name = f"{name} – Day Tour"
            # Check if default already exists for this region
            existing_default = ItineraryTemplate.objects.filter(region=region, is_default=True).first()
            if not existing_default:
                tmpl1, _ = ItineraryTemplate.objects.get_or_create(
                    region=region,
                    name=tmpl1_name,
                    defaults={
                        "country": country,
                        "code": _code(),
                        "includes_night": False,
                        "is_default": True,
                        "is_active": True,
                        "description": f"A full day tour of {name}. Perfect for day-trippers or multi-city plans.",
                        "created_by": admin,
                    }
                )
                self._attach_day_tour(tmpl1, day_tour)
                self._attach_incl_excl(tmpl1, incl_list, excl_list)
            else:
                tmpl1 = existing_default

            # Template 2: Day + Night
            tmpl2_name = f"{name} – Day & Night Stay"
            tmpl2, _ = ItineraryTemplate.objects.get_or_create(
                region=region,
                name=tmpl2_name,
                defaults={
                    "country": country,
                    "code": _code(),
                    "includes_night": True,
                    "is_default": False,
                    "is_active": True,
                    "description": f"Full day + overnight stay in {name}. Includes evening leisure time.",
                    "created_by": admin,
                }
            )
            self._attach_day_tour(tmpl2, day_tour)
            self._attach_incl_excl(tmpl2, incl_list, excl_list)

            self.stdout.write(f"    - {name} - tour + 2 templates")

    def _get_or_create_day_tour(self, region, activity_combination, unique_code,
                                 itinerary_text, est_time_distance):
        """Get or create a DayTour using raw SQL to satisfy legacy NOT NULL columns."""
        existing = DayTour.objects.filter(
            region=region,
            activity_combination=activity_combination
        ).first()
        if existing:
            return existing

        from django.utils import timezone
        now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO day_tours (
                    unique_code, region_id, activity_combination,
                    itinerary_text, est_time_distance,
                    display_order, is_active, currency,
                    includes_night, is_default,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                unique_code, region.id, activity_combination,
                itinerary_text, est_time_distance or "",
                0, True, "INR",
                False, False,
                now, now,
            ])
            tour_id = cursor.lastrowid
        return DayTour.objects.get(id=tour_id)

    def _attach_day_tour(self, template, day_tour):
        ItineraryTemplateDay.objects.get_or_create(
            template=template,
            day_number=1,
            defaults={"day_tour": day_tour}
        )

    def _attach_incl_excl(self, template, incl_list, excl_list):
        # Attach all inclusions and exclusions to each template
        for ie in incl_list:
            ItineraryTemplateInclExcl.objects.get_or_create(template=template, incl_excl=ie)
        for ie in excl_list:
            ItineraryTemplateInclExcl.objects.get_or_create(template=template, incl_excl=ie)
