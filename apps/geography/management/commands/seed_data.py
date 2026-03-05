"""
Seed sample data for Switzerland and Iceland.
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from apps.geography.models import Country, Region
from apps.attractions.models import Attraction
from apps.hotel.models import Hotel
from apps.day_tours.models import DayTour, DayTourAttraction
from apps.inclusions.models import InclExclCategory, InclusionExclusion
from apps.itinerary_templates.models import ItineraryTemplate, ItineraryTemplateDay
from apps.account.models import User


# ─────────────────────────── STATIC DATA ───────────────────────────

SWITZERLAND_REGIONS = [
    ("Zurich & Surroundings", "ZRH"),
    ("Lucerne & Central Switzerland", "LUC"),
    ("Interlaken & Bernese Oberland", "INT"),
    ("Zermatt & Valais", "ZER"),
    ("Geneva & Lake Geneva", "GVA"),
]

ICELAND_REGIONS = [
    ("Reykjavik & Capital Region", "REK"),
    ("Golden Circle", "GCR"),
    ("South Coast", "SCO"),
    ("East Fjords", "EFJ"),
    ("North Iceland & Akureyri", "NIK"),
]

SWITZERLAND_ATTRACTIONS = [
    # (region_idx, ref, name, lat, lng, notes)
    (0, "CH-ZRH-01", "Old Town (Altstadt)", 47.3722, 8.5414, "Medieval streets along the Limmat river"),
    (0, "CH-ZRH-02", "Lake Zurich Promenade", 47.3540, 8.5455, "Scenic lakeside walk with Alpine views"),
    (0, "CH-ZRH-03", "Bahnhofstrasse", 47.3690, 8.5390, "One of the world's most exclusive shopping streets"),
    (0, "CH-ZRH-04", "Kunsthaus Zurich", 47.3702, 8.5486, "Premier art museum with modern and classic collections"),
    (1, "CH-LUC-01", "Chapel Bridge (Kapellbrücke)", 47.0515, 8.3075, "Iconic 14th-century covered wooden bridge"),
    (1, "CH-LUC-02", "Lion Monument", 47.0585, 8.3108, "Carved rock sculpture commemorating Swiss Guards"),
    (1, "CH-LUC-03", "Mount Pilatus", 46.9789, 8.2525, "Dramatic peak with panoramic views, cogwheel railway"),
    (1, "CH-LUC-04", "Lake Lucerne Cruise", 47.0468, 8.3101, "Scenic steamboat ride across the stunning lake"),
    (2, "CH-INT-01", "Jungfraujoch – Top of Europe", 46.5472, 7.9853, "Highest railway station in Europe at 3,454m"),
    (2, "CH-INT-02", "Harder Kulm Viewpoint", 46.6926, 7.8612, "Panoramic terrace above Interlaken"),
    (2, "CH-INT-03", "Grindelwald First", 46.6610, 8.0516, "Alpine adventures: cliff walk, zip line, cart ride"),
    (2, "CH-INT-04", "Lake Brienz", 46.7283, 7.9615, "Turquoise glacial lake with Giessbach Falls"),
    (3, "CH-ZER-01", "Matterhorn Glacier Paradise", 45.9375, 7.7306, "Cable car to 3,883m with panoramic platform"),
    (3, "CH-ZER-02", "Gornergrat Railway", 45.9836, 7.7847, "Scenic cog railway with Matterhorn views"),
    (3, "CH-ZER-03", "Zermatt Village Walk", 45.9763, 7.6586, "Car-free village with charming chalet architecture"),
    (3, "CH-ZER-04", "Schwarzsee (Black Lake)", 45.9613, 7.7143, "Alpine lake below the Matterhorn's north face"),
    (4, "CH-GVA-01", "Jet d'Eau Fountain", 46.2073, 6.1554, "140m water jet on Lake Geneva"),
    (4, "CH-GVA-02", "Château de Chillon", 46.4142, 6.9273, "Medieval island castle on Lake Geneva shore"),
    (4, "CH-GVA-03", "Lavaux Vineyards", 46.4872, 6.7319, "UNESCO terraced vineyards above the lake"),
    (4, "CH-GVA-04", "United Nations Office", 46.2268, 6.1408, "Palais des Nations – guided tours available"),
]

ICELAND_ATTRACTIONS = [
    (0, "IS-REK-01", "Hallgrímskirkja Church", 64.1418, -21.9268, "Iconic Reykjavik church with observation tower"),
    (0, "IS-REK-02", "Harpa Concert Hall", 64.1505, -21.9326, "Award-winning glass concert hall on the harbor"),
    (0, "IS-REK-03", "Sun Voyager Sculpture", 64.1476, -21.9223, "Stainless steel Viking ship sculpture on waterfront"),
    (0, "IS-REK-04", "Laugavegur Street", 64.1453, -21.9260, "Main shopping and café street in downtown Reykjavik"),
    (1, "IS-GCR-01", "Þingvellir National Park", 64.2559, -21.1299, "UNESCO site where tectonic plates meet"),
    (1, "IS-GCR-02", "Geysir Geothermal Area", 64.3104, -20.3024, "Home of the original Geysir and active Strokkur"),
    (1, "IS-GCR-03", "Gullfoss Waterfall", 64.3271, -20.1199, "Massive two-tiered waterfall on Hvítá river"),
    (1, "IS-GCR-04", "Kerið Volcanic Crater", 64.0413, -20.8852, "Colorful 3,000-year-old volcanic crater lake"),
    (2, "IS-SCO-01", "Seljalandsfoss Waterfall", 63.6156, -19.9886, "Unique waterfall you can walk behind"),
    (2, "IS-SCO-02", "Skógafoss Waterfall", 63.5321, -19.5114, "Powerful 60m waterfall with rainbow views"),
    (2, "IS-SCO-03", "Reynisfjara Black Sand Beach", 63.4049, -19.0696, "Dramatic basalt columns and black sand"),
    (2, "IS-SCO-04", "Vík í Mýrdal Village", 63.4186, -19.0060, "Charming village beneath Mýrdalsjökull glacier"),
    (3, "IS-EFJ-01", "Vestrahorn Mountain", 64.2652, -15.0166, "Dramatic horn-shaped peak on Stokksnes peninsula"),
    (3, "IS-EFJ-02", "Djúpivogur Fishing Village", 64.6561, -14.2624, "Quaint harbor town with Eggin í Gleðivík art"),
    (3, "IS-EFJ-03", "Lagarfljót Lake", 65.0785, -14.3802, "Legendary lake rumored to have a monster"),
    (3, "IS-EFJ-04", "Hallormsstaður Forest", 65.0917, -14.7458, "Iceland's largest national forest"),
    (4, "IS-NIK-01", "Goðafoss Waterfall", 65.6828, -17.5502, "Waterfall of the Gods – stunning horseshoe falls"),
    (4, "IS-NIK-02", "Lake Mývatn", 65.6035, -16.9964, "Volcanic lake with diverse bird life and lava fields"),
    (4, "IS-NIK-03", "Akureyri Botanical Garden", 65.6781, -18.0929, "Northernmost botanical garden in the world"),
    (4, "IS-NIK-04", "Húsavík Whale Watching", 66.0449, -17.3383, "Europe's whale watching capital"),
]

SWITZERLAND_HOTELS = [
    # (region_idx, name, stars, lat, lng, city, email, phone, checkin, checkout)
    (0, "Hotel Schweizerhof Zurich", 5, 47.3769, 8.5400, "Zurich", "info@schweizerhof.ch", "+41 44 218 88 88", "15:00", "11:00"),
    (0, "Hotel Felix Zurich", 3, 47.3795, 8.5442, "Zurich", "hello@hotelfelix.ch", "+41 44 252 38 48", "14:00", "11:00"),
    (0, "25hours Hotel Zürich Langstrasse", 4, 47.3781, 8.5289, "Zurich", "zuerich@25hours-hotels.com", "+41 44 577 25 25", "15:00", "12:00"),
    (1, "Hotel des Balances", 4, 47.0518, 8.3077, "Lucerne", "info@balances.ch", "+41 41 418 28 28", "15:00", "11:00"),
    (1, "Grand Hotel National", 5, 47.0530, 8.3052, "Lucerne", "info@grandhotel-national.ch", "+41 41 419 09 09", "14:00", "12:00"),
    (1, "Hotel Pilatus-Kulm", 3, 46.9792, 8.2535, "Pilatus", "info@pilatus.ch", "+41 41 329 11 11", "14:00", "10:00"),
    (2, "Victoria-Jungfrau Grand Hotel", 5, 46.6864, 7.8614, "Interlaken", "info@victoria-jungfrau.ch", "+41 33 828 28 28", "15:00", "12:00"),
    (2, "Hotel Chalet Swiss", 3, 46.6890, 7.8527, "Interlaken", "hello@chaletswiss.ch", "+41 33 822 23 23", "14:00", "11:00"),
    (2, "Belvedere Swiss Quality Hotel", 4, 46.6555, 8.0349, "Grindelwald", "info@belvedere-grindelwald.ch", "+41 33 854 54 54", "15:00", "11:00"),
    (3, "Grand Hotel Zermatterhof", 5, 45.9768, 7.6585, "Zermatt", "info@zermatterhof.ch", "+41 27 966 66 00", "15:00", "11:00"),
    (3, "Hotel Pollux Zermatt", 3, 45.9760, 7.6595, "Zermatt", "info@hotelpollux.ch", "+41 27 966 40 00", "14:00", "10:30"),
    (4, "Hotel Beau-Rivage Geneva", 5, 46.2083, 6.1524, "Geneva", "info@beau-rivage.ch", "+41 22 716 66 66", "15:00", "12:00"),
    (4, "Hotel de la Paix Geneva", 4, 46.2067, 6.1500, "Geneva", "info@roccoforte-delapaix.ch", "+41 22 909 60 00", "15:00", "12:00"),
]

ICELAND_HOTELS = [
    (0, "Hotel Borg Reykjavik", 4, 64.1468, -21.9356, "Reykjavik", "info@hotelborg.is", "+354 551 1440", "14:00", "11:00"),
    (0, "Canopy by Hilton Reykjavik", 4, 64.1462, -21.9305, "Reykjavik", "reykjavik@hilton.com", "+354 528 7000", "15:00", "12:00"),
    (0, "Kex Hostel Reykjavik", 3, 64.1490, -21.9255, "Reykjavik", "hello@kexhostel.is", "+354 561 6060", "14:00", "11:00"),
    (1, "Ion Adventure Hotel", 4, 64.2380, -21.2230, "Selfoss", "info@ioniceland.is", "+354 482 3415", "15:00", "11:00"),
    (1, "Hotel Geysir", 3, 64.3110, -20.3020, "Geysir", "info@hotelgeysir.is", "+354 480 6800", "14:00", "11:00"),
    (2, "Hotel Rangá", 4, 63.6580, -20.2300, "Hella", "hotelranga@hotelranga.is", "+354 487 5700", "15:00", "12:00"),
    (2, "Hotel Katla", 3, 63.4188, -19.0075, "Vík", "info@hotelkatla.is", "+354 487 1208", "14:00", "11:00"),
    (2, "Dyrhólaey Guesthouse", 3, 63.4010, -19.1285, "Vík", "dyrhol@simnet.is", "+354 487 1333", "14:00", "11:00"),
    (3, "Fosshotel Eastfjords", 3, 64.6565, -14.2620, "Djúpivogur", "eastfjords@fosshotel.is", "+354 478 8886", "14:00", "11:00"),
    (3, "Hótel Hallormsstaður", 3, 65.0920, -14.7460, "Egilsstaðir", "hallormsstadur@hotellex.is", "+354 471 2400", "14:00", "11:00"),
    (4, "Hotel Kea Akureyri", 4, 65.6825, -18.0900, "Akureyri", "info@keahotels.is", "+354 460 2000", "14:00", "11:00"),
    (4, "Fosshotel Húsavík", 3, 66.0445, -17.3390, "Húsavík", "husavik@fosshotel.is", "+354 464 1220", "14:00", "11:00"),
    (4, "Fosshotel Mývatn", 3, 65.6330, -16.9130, "Mývatn", "myvatn@fosshotel.is", "+354 464 4164", "14:00", "11:00"),
]

SWITZERLAND_DAY_TOURS = [
    # (region_idx, code, activity, itinerary_text, attraction_indices)
    (0, "CH-DT-01", "Zurich Old Town & Lake Walk",
     "Morning walk through Altstadt, visit Kunsthaus, afternoon stroll along Lake Zurich Promenade. End at Bahnhofstrasse for shopping.",
     [0, 1, 2, 3]),
    (1, "CH-DT-02", "Lucerne Highlights & Mount Pilatus",
     "Start at Chapel Bridge, visit Lion Monument, take cogwheel railway to Mount Pilatus summit. Afternoon cruise on Lake Lucerne.",
     [4, 5, 6, 7]),
    (2, "CH-DT-03", "Jungfraujoch Excursion",
     "Full-day trip to Jungfraujoch Top of Europe. Stop at Harder Kulm for valley views. Return via Grindelwald.",
     [8, 9, 10]),
    (2, "CH-DT-04", "Grindelwald First & Lake Brienz",
     "Morning at Grindelwald First for cliff walk and adventure activities. Afternoon boat ride on turquoise Lake Brienz.",
     [10, 11]),
    (3, "CH-DT-05", "Matterhorn Day – Gornergrat & Village",
     "Scenic Gornergrat railway ride with Matterhorn views. Walk to Schwarzsee. Evening stroll through car-free Zermatt.",
     [12, 13, 14, 15]),
    (4, "CH-DT-06", "Geneva City & Château de Chillon",
     "Morning at Jet d'Eau and UN Office. Drive along Lake Geneva to Château de Chillon. Wine tasting in Lavaux.",
     [16, 17, 18, 19]),
]

ICELAND_DAY_TOURS = [
    (0, "IS-DT-01", "Reykjavik City Discovery",
     "Explore Hallgrímskirkja church tower, walk to Harpa Concert Hall. Visit Sun Voyager sculpture. Shopping on Laugavegur Street.",
     [0, 1, 2, 3]),
    (1, "IS-DT-02", "Classic Golden Circle Tour",
     "Þingvellir tectonic plates, watch Strokkur erupt at Geysir, marvel at Gullfoss waterfall. Stop at Kerið crater.",
     [4, 5, 6, 7]),
    (2, "IS-DT-03", "South Coast Waterfalls & Black Beach",
     "Walk behind Seljalandsfoss, stand before powerful Skógafoss. Explore Reynisfjara basalt columns. Visit Vík village.",
     [8, 9, 10, 11]),
    (3, "IS-DT-04", "East Fjords Scenic Drive",
     "Drive to dramatic Vestrahorn mountain. Visit Djúpivogur harbor art. Lunch at lake-side café near Lagarfljót.",
     [12, 13, 14]),
    (3, "IS-DT-05", "Hallormsstaður Forest & Lake",
     "Nature walk through Iceland's largest forest. Scenic boat ride on Lagarfljót lake. Picnic lunch.",
     [14, 15]),
    (4, "IS-DT-06", "Akureyri, Goðafoss & Lake Mývatn",
     "Visit Goðafoss waterfall. Explore Lake Mývatn volcanic landscape. Visit Akureyri Botanical Garden.",
     [16, 17, 18]),
    (4, "IS-DT-07", "Húsavík Whale Watching Adventure",
     "Whale watching tour from Húsavík harbor. Visit whale museum. Lunch at harbor restaurants. Visit Goðafoss on return.",
     [16, 19]),
]

INCL_EXCL_CATEGORIES = [
    "Transport", "Accommodation", "Meals", "Activities & Excursions",
    "Guide & Assistance", "Transfers", "Insurance", "Visa & Documentation",
]

SWITZERLAND_INCLUSIONS = [
    # (cat_idx, code, type, item_service, details)
    (0, "CH-INC-01", "INCLUSION", "Swiss Travel Pass (2nd class)", "Unlimited travel on trains, buses, boats for trip duration"),
    (1, "CH-INC-02", "INCLUSION", "Hotel accommodation with breakfast", "3-4 star hotels, twin sharing basis"),
    (2, "CH-INC-03", "INCLUSION", "Daily breakfast at hotel", "Continental or buffet breakfast included"),
    (3, "CH-INC-04", "INCLUSION", "Jungfraujoch excursion ticket", "Round-trip train ticket to Top of Europe"),
    (3, "CH-INC-05", "INCLUSION", "Mount Pilatus Golden Round Trip", "Boat + cogwheel train + cable car circuit"),
    (4, "CH-INC-06", "INCLUSION", "English-speaking tour guide", "Licensed local guide for city tours"),
    (5, "CH-INC-07", "INCLUSION", "Airport transfers (Zurich)", "Private car Zurich airport to hotel and return"),
    (3, "CH-INC-08", "INCLUSION", "Lake Lucerne steamboat cruise", "1-hour scenic cruise included"),
    (2, "CH-EXC-01", "EXCLUSION", "Lunch and dinner", "Not included unless specified"),
    (6, "CH-EXC-02", "EXCLUSION", "Travel insurance", "Personal travel insurance not included"),
    (7, "CH-EXC-03", "EXCLUSION", "Visa fees", "Swiss/Schengen visa fees are extra"),
    (3, "CH-EXC-04", "EXCLUSION", "Paragliding in Interlaken", "Optional adventure activity at own cost"),
    (0, "CH-EXC-05", "EXCLUSION", "First class rail upgrade", "Upgrade to 1st class at extra charge"),
]

ICELAND_INCLUSIONS = [
    (0, "IS-INC-01", "INCLUSION", "4x4 vehicle rental with insurance", "SUV rental with CDW and gravel protection"),
    (1, "IS-INC-02", "INCLUSION", "Guesthouse & hotel stays", "3-star accommodation with breakfast"),
    (2, "IS-INC-03", "INCLUSION", "Daily breakfast at accommodation", "Full Icelandic breakfast included"),
    (3, "IS-INC-04", "INCLUSION", "Golden Circle guided tour", "Full-day guided tour with transport"),
    (3, "IS-INC-05", "INCLUSION", "Whale watching from Húsavík", "3-hour whale watching boat tour"),
    (4, "IS-INC-06", "INCLUSION", "Local guide for South Coast", "Experienced English-speaking guide"),
    (5, "IS-INC-07", "INCLUSION", "Keflavík Airport transfer", "Shared shuttle to/from Reykjavik"),
    (3, "IS-INC-08", "INCLUSION", "Blue Lagoon entry (Comfort)", "Comfort package entry to Blue Lagoon"),
    (2, "IS-EXC-01", "EXCLUSION", "Lunch and dinner meals", "Meals other than breakfast not included"),
    (6, "IS-EXC-02", "EXCLUSION", "Travel insurance", "Not included — highly recommended"),
    (3, "IS-EXC-03", "EXCLUSION", "Glacier hiking excursion", "Optional glacier walk at extra cost"),
    (3, "IS-EXC-04", "EXCLUSION", "Snowmobile on Langjökull", "Optional glacier snowmobile tour"),
    (0, "IS-EXC-05", "EXCLUSION", "Fuel for rental car", "Petrol/diesel not included in rental"),
]


class Command(BaseCommand):
    help = "Seed sample data for Switzerland and Iceland (20+ records per entity)"

    def handle(self, *args, **options):
        self.stdout.write("🌱 Seeding data...\n")

        admin = User.objects.filter(is_staff=True).first()

        # ── Countries ──
        ch, _ = Country.objects.get_or_create(code="CHE", defaults={"name": "Switzerland", "iso_code": "CHE"})
        ic, _ = Country.objects.get_or_create(code="ISL", defaults={"name": "Iceland", "iso_code": "ISL"})
        self.stdout.write(f"  ✓ Countries: {ch.name}, {ic.name}")

        # ── Regions ──
        ch_regions = []
        for i, (name, code) in enumerate(SWITZERLAND_REGIONS):
            r, _ = Region.objects.get_or_create(country=ch, code=code, defaults={"name": name, "display_order": i})
            ch_regions.append(r)

        ic_regions = []
        for i, (name, code) in enumerate(ICELAND_REGIONS):
            r, _ = Region.objects.get_or_create(country=ic, code=code, defaults={"name": name, "display_order": i})
            ic_regions.append(r)
        self.stdout.write(f"  ✓ Regions: {len(ch_regions)} CH + {len(ic_regions)} IS")

        # ── Attractions ──
        ch_attractions = []
        for ridx, ref, name, lat, lng, notes in SWITZERLAND_ATTRACTIONS:
            a, _ = Attraction.objects.get_or_create(
                reference_no=ref,
                defaults={"region": ch_regions[ridx], "name": name, "latitude": lat, "longitude": lng,
                           "key_features_notes": notes, "display_order": len(ch_attractions)},
            )
            ch_attractions.append(a)

        ic_attractions = []
        for ridx, ref, name, lat, lng, notes in ICELAND_ATTRACTIONS:
            a, _ = Attraction.objects.get_or_create(
                reference_no=ref,
                defaults={"region": ic_regions[ridx], "name": name, "latitude": lat, "longitude": lng,
                           "key_features_notes": notes, "display_order": len(ic_attractions)},
            )
            ic_attractions.append(a)
        self.stdout.write(f"  ✓ Attractions: {len(ch_attractions)} CH + {len(ic_attractions)} IS")

        # ── Hotels ──
        ch_hotels = []
        for ridx, name, stars, lat, lng, city, email, phone, ci, co in SWITZERLAND_HOTELS:
            h, _ = Hotel.objects.get_or_create(
                name=name, country=ch,
                defaults={"region": ch_regions[ridx], "star_rating": stars, "latitude": lat, "longitude": lng,
                           "city": city, "contact_email": email, "contact_phone": phone,
                           "check_in_time": ci, "check_out_time": co, "display_order": len(ch_hotels)},
            )
            ch_hotels.append(h)

        ic_hotels = []
        for ridx, name, stars, lat, lng, city, email, phone, ci, co in ICELAND_HOTELS:
            h, _ = Hotel.objects.get_or_create(
                name=name, country=ic,
                defaults={"region": ic_regions[ridx], "star_rating": stars, "latitude": lat, "longitude": lng,
                           "city": city, "contact_email": email, "contact_phone": phone,
                           "check_in_time": ci, "check_out_time": co, "display_order": len(ic_hotels)},
            )
            ic_hotels.append(h)
        self.stdout.write(f"  ✓ Hotels: {len(ch_hotels)} CH + {len(ic_hotels)} IS")

        # ── Day Tours ──
        ch_daytours = []
        for ridx, code, activity, text, attr_indices in SWITZERLAND_DAY_TOURS:
            dt, created = DayTour.objects.get_or_create(
                unique_code=code,
                defaults={"region": ch_regions[ridx], "activity_combination": activity,
                           "itinerary_text": text, "created_by": admin,
                           "display_order": len(ch_daytours)},
            )
            if created:
                for order, ai in enumerate(attr_indices, 1):
                    DayTourAttraction.objects.get_or_create(
                        day_tour=dt, attraction=ch_attractions[ai], defaults={"visit_order": order})
            ch_daytours.append(dt)

        ic_daytours = []
        for ridx, code, activity, text, attr_indices in ICELAND_DAY_TOURS:
            dt, created = DayTour.objects.get_or_create(
                unique_code=code,
                defaults={"region": ic_regions[ridx], "activity_combination": activity,
                           "itinerary_text": text, "created_by": admin,
                           "display_order": len(ic_daytours)},
            )
            if created:
                for order, ai in enumerate(attr_indices, 1):
                    DayTourAttraction.objects.get_or_create(
                        day_tour=dt, attraction=ic_attractions[ai], defaults={"visit_order": order})
            ic_daytours.append(dt)
        self.stdout.write(f"  ✓ Day Tours: {len(ch_daytours)} CH + {len(ic_daytours)} IS")

        # ── Inclusion/Exclusion Categories ──
        categories = []
        for i, name in enumerate(INCL_EXCL_CATEGORIES):
            cat, _ = InclExclCategory.objects.get_or_create(name=name, defaults={"display_order": i})
            categories.append(cat)
        self.stdout.write(f"  ✓ Incl/Excl Categories: {len(categories)}")

        # ── Inclusions & Exclusions ──
        ch_ie = []
        for cat_idx, code, ie_type, item, details in SWITZERLAND_INCLUSIONS:
            obj, _ = InclusionExclusion.objects.get_or_create(
                unique_code=code,
                defaults={"country": ch, "type": ie_type, "category": categories[cat_idx],
                           "item_service": item, "details_notes": details,
                           "display_order": len(ch_ie)},
            )
            ch_ie.append(obj)

        ic_ie = []
        for cat_idx, code, ie_type, item, details in ICELAND_INCLUSIONS:
            obj, _ = InclusionExclusion.objects.get_or_create(
                unique_code=code,
                defaults={"country": ic, "type": ie_type, "category": categories[cat_idx],
                           "item_service": item, "details_notes": details,
                           "display_order": len(ic_ie)},
            )
            ic_ie.append(obj)
        self.stdout.write(f"  ✓ Inclusions/Exclusions: {len(ch_ie)} CH + {len(ic_ie)} IS")

        # ── Itinerary Templates ──
        # Switzerland 7N/8D
        ch_tmpl, ch_created = ItineraryTemplate.objects.get_or_create(
            code="CH-7N8D-CLASSIC",
            defaults={"country": ch, "name": "Classic Switzerland 7 Nights",
                       "total_nights": 7, "total_days": 8,
                       "description": "Zurich → Lucerne → Interlaken → Zermatt → Geneva. The ultimate Swiss experience.",
                       "created_by": admin},
        )
        if ch_created:
            ch_tmpl_days = [
                (1, ch_daytours[0], True, False),   # Zurich city
                (2, ch_daytours[1], False, False),   # Lucerne + Pilatus
                (3, ch_daytours[2], False, False),   # Jungfraujoch
                (4, ch_daytours[3], False, False),   # Grindelwald + Brienz
                (5, ch_daytours[4], False, False),   # Matterhorn day
                (6, ch_daytours[5], False, False),   # Geneva + Chillon
                (7, ch_daytours[0], False, False),   # Free day in Zurich
                (8, ch_daytours[0], False, True),    # Departure
            ]
            for dn, dt, arr, dep in ch_tmpl_days:
                ItineraryTemplateDay.objects.get_or_create(
                    template=ch_tmpl, day_number=dn,
                    defaults={"day_tour": dt, "is_arrival_day": arr, "is_departure_day": dep})

        # Switzerland 4N/5D
        ch_tmpl2, ch2_created = ItineraryTemplate.objects.get_or_create(
            code="CH-4N5D-EXPRESS",
            defaults={"country": ch, "name": "Express Switzerland 4 Nights",
                       "total_nights": 4, "total_days": 5,
                       "description": "Zurich → Lucerne → Interlaken → Zurich. Best of Switzerland in 5 days.",
                       "created_by": admin},
        )
        if ch2_created:
            for dn, dt, arr, dep in [(1, ch_daytours[0], True, False), (2, ch_daytours[1], False, False),
                                       (3, ch_daytours[2], False, False), (4, ch_daytours[3], False, False),
                                       (5, ch_daytours[0], False, True)]:
                ItineraryTemplateDay.objects.get_or_create(
                    template=ch_tmpl2, day_number=dn,
                    defaults={"day_tour": dt, "is_arrival_day": arr, "is_departure_day": dep})

        # Iceland 6N/7D
        ic_tmpl, ic_created = ItineraryTemplate.objects.get_or_create(
            code="IS-6N7D-RINGROAD",
            defaults={"country": ic, "name": "Iceland Ring Road 6 Nights",
                       "total_nights": 6, "total_days": 7,
                       "description": "Reykjavik → Golden Circle → South Coast → East Fjords → North → Reykjavik. Full circle.",
                       "created_by": admin},
        )
        if ic_created:
            ic_tmpl_days = [
                (1, ic_daytours[0], True, False),   # Reykjavik
                (2, ic_daytours[1], False, False),   # Golden Circle
                (3, ic_daytours[2], False, False),   # South Coast
                (4, ic_daytours[3], False, False),   # East Fjords
                (5, ic_daytours[5], False, False),   # Akureyri + Goðafoss
                (6, ic_daytours[6], False, False),   # Húsavík whales
                (7, ic_daytours[0], False, True),    # Departure
            ]
            for dn, dt, arr, dep in ic_tmpl_days:
                ItineraryTemplateDay.objects.get_or_create(
                    template=ic_tmpl, day_number=dn,
                    defaults={"day_tour": dt, "is_arrival_day": arr, "is_departure_day": dep})

        # Iceland 4N/5D
        ic_tmpl2, ic2_created = ItineraryTemplate.objects.get_or_create(
            code="IS-4N5D-SOUTH",
            defaults={"country": ic, "name": "South Iceland & Golden Circle 4 Nights",
                       "total_nights": 4, "total_days": 5,
                       "description": "Reykjavik → Golden Circle → South Coast → Reykjavik. Best of southern Iceland.",
                       "created_by": admin},
        )
        if ic2_created:
            for dn, dt, arr, dep in [(1, ic_daytours[0], True, False), (2, ic_daytours[1], False, False),
                                       (3, ic_daytours[2], False, False), (4, ic_daytours[4], False, False),
                                       (5, ic_daytours[0], False, True)]:
                ItineraryTemplateDay.objects.get_or_create(
                    template=ic_tmpl2, day_number=dn,
                    defaults={"day_tour": dt, "is_arrival_day": arr, "is_departure_day": dep})

        self.stdout.write(f"  ✓ Templates: 2 CH + 2 IS (with days)")

        # ── Summary ──
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Seeding complete!\n"
            f"   Countries: 2\n"
            f"   Regions: {len(ch_regions) + len(ic_regions)}\n"
            f"   Attractions: {len(ch_attractions) + len(ic_attractions)}\n"
            f"   Hotels: {len(ch_hotels) + len(ic_hotels)}\n"
            f"   Day Tours: {len(ch_daytours) + len(ic_daytours)}\n"
            f"   Incl/Excl Categories: {len(categories)}\n"
            f"   Inclusions/Exclusions: {len(ch_ie) + len(ic_ie)}\n"
            f"   Templates: 4\n"
        ))
