"""
Management command: seed_demo_data

Clears and re-seeds Switzerland & Iceland with:
  - 30 regions each
  - 1 day tour per region (with 3-4 attractions) — INR prices
  - 3 templates per region (Solo Day, Couple Night, Group Day)
  - 15 inclusions + 12 exclusions per country
  - ~20 hotels per country
  - All prices in INR

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
from apps.hotel.models import Hotel
from apps.itinerary_templates.models import (
    ItineraryTemplate, ItineraryTemplateDay, ItineraryTemplateInclExcl,
)
from apps.account.models import User

# ──────────────────────────────────────────────────────────────────────────────
  # REGION DATA — 30 per country
# ──────────────────────────────────────────────────────────────────────────────

SWITZERLAND_REGIONS = [
    ("ZUR", "Zurich & Surroundings",
     "Switzerland's largest city — old town, Lake Zurich, and world-class museums."),
    ("LUC", "Lucerne & Central Switzerland",
     "Lakeside city with the Chapel Bridge and stunning mountain backdrop."),
    ("BER", "Bern & Bernese Oberland",
     "UNESCO old town, the Swiss capital, gateway to Jungfrau region."),
    ("INT", "Interlaken & Jungfrau",
     "Adventure hub between lakes Thun and Brienz, gateway to Jungfraujoch."),
    ("GEN", "Geneva & Lake Geneva",
     "International city with Jet d'Eau, UN headquarters, and lakefront charm."),
    ("LAU", "Lausanne & Lavaux",
     "Olympic Museum, terraced vineyards, and French-Swiss culture."),
    ("ZER", "Zermatt & Matterhorn",
     "Car-free alpine village beneath the iconic Matterhorn peak."),
    ("STG", "St. Gallen & Rhine Falls",
     "Baroque abbey library, Rhine Falls, and traditional countryside."),
    ("DAV", "Davos & Klosters",
     "High-altitude resort known for skiing and the World Economic Forum."),
    ("MON", "Montreux & Vevey",
     "Jazz Festival city, Chillon Castle, and subtropical Lake Geneva shores."),
    ("BAS", "Basel & Rhine Valley",
     "Art Basel, world-class museums, and Rhine river promenade."),
    ("AND", "Andermatt & Gotthard",
     "Alpine crossroads with Gotthard Pass and pristine ski terrain."),
    ("MEI", "Meiringen & Hasliberg",
     "Aare Gorge, Reichenbach Falls, and Sherlock Holmes Museum."),
    ("SAA", "Saas-Fee & Saas Valley",
     "Glacier village with year-round skiing at 3,500 m altitude."),
    ("LOC", "Locarno & Ascona",
     "Italian-speaking Ticino with palm trees and Piazza Grande."),
    ("LUG", "Lugano & Lake Lugano",
     "Mediterranean flair meets alpine scenery, Monte Brè funicular."),
    ("GRD", "Grindelwald & Eiger",
     "Alpine village beneath the Eiger North Face, FIRST cliff walk."),
    ("SOL", "Solothurn & Aare Region",
     "Baroque city of ambassadors with St. Ursus Cathedral."),
    ("FRI", "Fribourg & Gruyère",
     "Medieval old town, Gottéron gorge, cheese and chocolate culture."),
    ("ENG", "Engadin & St. Moritz",
     "High valley with turquoise lakes and St. Moritz glamour."),
    ("THU", "Thun & Lake Thun",
     "Castle town on glittering Lake Thun with Alpine panorama."),
    ("APP", "Appenzell & Alpstein",
     "Traditional village with painted houses and Ebenalp cliff faces."),
    ("LAT", "Lauterbrunnen Valley",
     "Valley of 72 waterfalls — Staubbach and Trümmelbach Falls."),
    ("ARO", "Arosa & Lenzerheide",
     "Year-round resort with bear sanctuary and forest trails."),
    ("VRB", "Verbier & 4 Vallées",
     "World-class ski resort with panoramic Mont Fort summit."),
    ("WEN", "Wengen & Männlichen",
     "Car-free village with Royal Walk and Eiger views."),
    ("BRZ", "Brienz & Rothorn",
     "Steam railway, wood carving tradition, and turquoise lake."),
    ("SIO", "Sion & Valais Wine",
     "Twin castles, Roman ruins, and Switzerland's sunniest wine region."),
    ("CRA", "Crans-Montana",
     "High plateau resort with golf, skiing, and panoramic trails."),
    ("PON", "Pontresina & Bernina",
     "Glacier trails, Bernina Express views, and Engadin alpine charm."),
]

ICELAND_REGIONS = [
    ("REY", "Reykjavik & Capital Region",
     "Iceland's vibrant capital with colourful houses and geothermal pools."),
    ("SNA", "Snæfellsnes Peninsula",
     "Snæfellsjökull glacier, Kirkjufell, and dramatic lava fields."),
    ("WFJ", "Westfjords",
     "Towering Látrabjarg bird cliffs, Arctic foxes, and mirror-calm fjords."),
    ("NOR", "North Iceland & Akureyri",
     "Whale watching capital, Goðafoss waterfall, and botanical gardens."),
    ("DIA", "Diamond Circle & Lake Mývatn",
     "Geothermal wonderland — pseudo-craters, Dimmuborgir, and mud pools."),
    ("EAS", "East Iceland & Eastfjords",
     "Rugged fjord scenery, reindeer herds, and seabird cliffs."),
    ("GCR", "Golden Circle",
     "Þingvellir, Geysir, and Gullfoss — Iceland's most famous route."),
    ("SOU", "South Coast",
     "Black sand beaches, Seljalandsfoss, Skógafoss, and glaciers."),
    ("VAT", "Vatnajökull & Jökulsárlón",
     "Europe's largest glacier, Diamond Beach, and ice caves."),
    ("VES", "Vestmannaeyjar Islands",
     "Volcanic archipelago with Eldfell volcano and puffin colonies."),
    ("LAK", "Lakagígar Highlands",
     "Remote 1783 Laki lava field, accessible Jun–Sep via F-roads."),
    ("KER", "Kerlingarfjöll Hot Springs",
     "Highland geothermal rhyolite mountains and natural hot tubs."),
    ("HEK", "Hekla & Southern Highlands",
     "Active volcano zone, lava tubes, and Landmannalaugar access."),
    ("AUR", "Aurora Trail & Northeast",
     "Best dark-sky zone for Northern Lights and rural culture."),
    ("PEN", "Reykjanes & Blue Lagoon",
     "Geothermal landscape, Blue Lagoon, and Bridge Between Continents."),
    ("THO", "Þórsmörk Valley",
     "Glacial valley, Fimmvörðuháls trek, and highland wildlife."),
    ("HOL", "Hólmavík & Strandir",
     "Sorcery museum, deserted coastlines, and seal watching."),
    ("ASK", "Askja & Highland Caldera",
     "Remote Viti crater lake, accessible via F-roads in summer."),
    ("GRM", "Grímsey & Arctic Circle",
     "Iceland's only Arctic Circle territory — puffins and midnight sun."),
    ("HUS", "Húsavík & Whale Coast",
     "Europe's whale watching capital with humpback whales."),
    ("LAN", "Landmannalaugar & Fjallabak",
     "Rainbow rhyolite mountains, natural hot pools, and lava deserts."),
    ("FJA", "Fjaðrárgljúfur Canyon",
     "Spectacular 100 m deep moss-covered canyon near Kirkjubæjarklaustur."),
    ("SKA", "Skaftafell & Öræfajökull",
     "Svartifoss basalt waterfall and glacier tongue hiking trails."),
    ("BOR", "Borgarfjörður & Reykholt",
     "Hraunfossar lava waterfalls and Snorri Sturluson's medieval estate."),
    ("SGF", "Siglufjörður & Troll Peninsula",
     "Herring Era Museum, dramatic tunnel drives, and fjord scenery."),
    ("DAL", "Dalvík & Eyjafjörður",
     "Arctic sea bathing, fishing culture, and longest fjord views."),
    ("FLA", "Flatey Island & Breiðafjörður",
     "Tiny heritage island with medieval church and seabird colonies."),
    ("HVT", "Hvítserkur & Vatnsnes",
     "15 m sea stack, seal colonies, and scenic peninsula drive."),
    ("DTF", "Dettifoss & Jökulsárgljúfur",
     "Europe's most powerful waterfall and horseshoe canyon Ásbyrgi."),
    ("STF", "Stöðvarfjörður & East Coast",
     "Petra's mineral collection, colourful harbours, and coastal hikes."),
]

# ──────────────────────────────────────────────────────────────────────────────
# DAY TOUR DATA — 1 per region  (name, activities, timing, price_inr)
# ──────────────────────────────────────────────────────────────────────────────

CH_TOURS = {
    "ZUR": ("Zurich City & Lake Tour",
            "Old Town Walk • Lake Zurich Cruise • Swiss National Museum • Bahnhofstrasse Shopping",
            "Full day — approx 8 hrs", 18000),
    "LUC": ("Lucerne Highlights & Lake Cruise",
            "Chapel Bridge • Lion Monument • Lake Lucerne Cruise • Glacier Garden",
            "Full day — approx 7 hrs", 16000),
    "BER": ("Bern Old Town & Rose Garden",
            "Federal Palace • Bear Park • Zytglogge Clock Tower • Rose Garden Viewpoint",
            "Full day — approx 7 hrs", 15000),
    "INT": ("Jungfraujoch — Top of Europe",
            "Jungfraujoch 3,454 m • Aletsch Glacier Viewpoint • Ice Palace • Sphinx Observatory",
            "Full day — approx 9 hrs", 35000),
    "GEN": ("Geneva City Tour & Jet d'Eau",
            "Jet d'Eau Fountain • Old Town Walk • Palais des Nations • Flower Clock",
            "Full day — approx 7 hrs", 16500),
    "LAU": ("Lavaux Vineyards UNESCO Walk",
            "Cully Village Walk • Lavaux Terraced Vineyards • Puidoux Viewpoint • Local Wine Tasting",
            "Half day — approx 5 hrs", 12000),
    "ZER": ("Matterhorn & Glacier Paradise",
            "Matterhorn Glacier Paradise 3,883 m • Ice Palace • Mountain Terrace • Zermatt Village Walk",
            "Full day — approx 9 hrs", 38000),
    "STG": ("Rhine Falls & St. Gallen Abbey",
            "Rhine Falls Panorama • St. Gallen Abbey Library • Old Town Oriel Windows Walk",
            "Full day — approx 8 hrs", 17000),
    "DAV": ("Davos Schatzalp & Forest Trail",
            "Schatzalp Botanical Garden • Davos Lake Walk • Seehorn Circular Hike",
            "Full day — approx 7 hrs", 14000),
    "MON": ("Montreux & Chillon Castle",
            "Château de Chillon Tour • Montreux Promenade • Queen Studio • Lake Geneva Cruise",
            "Full day — approx 8 hrs", 19000),
    "BAS": ("Basel Museum Quarter & Rhine",
            "Kunstmuseum Basel • Mittlere Rheinbrücke Walk • Basel Minster • Rhine Riverbank",
            "Full day — approx 7 hrs", 15500),
    "AND": ("Andermatt & Devil's Bridge",
            "Devil's Bridge • Schöllenen Gorge • Gotthard Pass Museum • Andermatt Village",
            "Full day — approx 8 hrs", 16000),
    "MEI": ("Aare Gorge & Reichenbach Falls",
            "Aare Gorge Walk • Reichenbach Falls • Sherlock Holmes Museum • Meiringen Village",
            "Half day — approx 5 hrs", 12500),
    "SAA": ("Saas-Fee Allalin Glacier",
            "Metro Alpin to 3,500 m • Allalin Glacier Walk • Ice Pavilion • Saas-Fee Village",
            "Full day — approx 9 hrs", 32000),
    "LOC": ("Locarno & Cardada Mountain",
            "Cardada Cimetta Cable Car • Piazza Grande • Madonna del Sasso Sanctuary • Lake Maggiore Views",
            "Full day — approx 7 hrs", 15000),
    "LUG": ("Lugano City & Monte Brè",
            "Monte Brè Funicular • Lugano Old Town • Parco Ciani Walk • Lugano Lake Boat Tour",
            "Full day — approx 8 hrs", 17500),
    "GRD": ("Grindelwald FIRST Cliff Walk",
            "FIRST Cliff Walk by Tissot • FIRST Flyer Zip Line • Bachalpsee Hike • Eiger North Face View",
            "Full day — approx 9 hrs", 28000),
    "SOL": ("Solothurn Baroque City Walk",
            "St. Ursus Cathedral • Old Armory • Eleven Towers Walk • Aare Riverside Promenade",
            "Half day — approx 4 hrs", 9000),
    "FRI": ("Fribourg Old Town & Gruyère",
            "Gottéron Gorge Walk • St. Nicolas Cathedral • Gruyère Castle • Chocolate Factory",
            "Full day — approx 7 hrs", 18000),
    "ENG": ("Engadin Lake & St. Moritz",
            "St. Moritz Village Walk • Engadin Lake Promenade • Maloja Pass Drive • Sils Maria Village",
            "Full day — approx 8 hrs", 22000),
    "THU": ("Thun Castle & Lake Cruise",
            "Thun Castle Museum • Lake Thun Panorama Cruise • Oberhofen Castle Gardens • Hünegg Castle",
            "Full day — approx 7 hrs", 16000),
    "APP": ("Appenzell Village & Ebenalp",
            "Appenzell Traditional Village • Ebenalp Cable Car • Wildkirchli Caves • Seealpsee Lake Hike",
            "Full day — approx 8 hrs", 17500),
    "LAT": ("Lauterbrunnen Valley Waterfalls",
            "Staubbach Falls Viewpoint • Trümmelbach Falls Inside • Valley Floor Walk • Mürren Cable Car",
            "Full day — approx 7 hrs", 19000),
    "ARO": ("Arosa Weisshorn & Bear Sanctuary",
            "Arosa Weisshorn Gondola • Bear Sanctuary Visit • Untersee Lake Trail • Alpine Panorama Walk",
            "Full day — approx 7 hrs", 15000),
    "VRB": ("Verbier Mountain Panorama",
            "Mont Fort Summit 3,330 m • High Alpine Trail • Verbier Village Walk • Le Châble Gondola",
            "Full day — approx 8 hrs", 24000),
    "WEN": ("Wengen Alpine Experience",
            "Wengen Village Walk • Männlichen Royal Walk • Kleine Scheidegg Station • Eiger North Face View",
            "Full day — approx 8 hrs", 21000),
    "BRZ": ("Brienz Rothorn Steam Train",
            "Rothorn Steam Railway • Lake Brienz Boat Tour • Wood Carving Museum • Giessbach Falls Visit",
            "Full day — approx 7 hrs", 20000),
    "SIO": ("Sion Castles & Wine Trail",
            "Valère Basilica Tour • Tourbillon Castle Hike • Old Town Walk • Valais Wine Tasting Trail",
            "Full day — approx 7 hrs", 14000),
    "CRA": ("Crans-Montana Alpine Views",
            "Cry d'Er Summit Gondola • Bisse du Ro Walk • Étang Long Lake • Montana Village Promenade",
            "Full day — approx 7 hrs", 16500),
    "PON": ("Pontresina Glacier & Bernina",
            "Morteratsch Glacier Trail • Muottas Muragl Panorama • Bernina Express Viewpoint • Pontresina Village",
            "Full day — approx 8 hrs", 23000),
}

IS_TOURS = {
    "REY": ("Reykjavik City & Hallgrímskirkja",
            "Hallgrímskirkja Church Tower • Harpa Concert Hall • Sun Voyager Sculpture • Old Harbour Walk",
            "Full day — approx 7 hrs", 15000),
    "SNA": ("Snæfellsnes & Kirkjufell",
            "Kirkjufell Mountain Photo Stop • Djúpalónssandur Beach • Arnarstapi Cliffs Walk • Snæfellsjökull Views",
            "Full day — approx 10 hrs", 22000),
    "WFJ": ("Látrabjarg Bird Cliffs",
            "Látrabjarg Puffin Cliffs • Rauðisandur Beach Walk • Dynjandi Waterfall • Remote Fjord Drive",
            "Full day — approx 12 hrs", 28000),
    "NOR": ("Goðafoss & Akureyri Gardens",
            "Goðafoss Waterfall • Akureyri Botanic Garden • Whale Watching Boat Tour",
            "Full day — approx 9 hrs", 24000),
    "DIA": ("Mývatn Nature Baths & Craters",
            "Mývatn Nature Baths • Dimmuborgir Lava Fields • Grjótagjá Cave • Krafla Caldera Walk",
            "Full day — approx 10 hrs", 20000),
    "EAS": ("Eastfjords Scenic Drive",
            "Djúpivogur Village • Petra's Stone Collection • Stöðvarfjörður Harbour • Reyðarfjörður Views",
            "Full day — approx 10 hrs", 18000),
    "GCR": ("Golden Circle Full Day",
            "Þingvellir National Park • Strokkur Geysir Eruptions • Gullfoss Waterfall • Kerið Crater Lake",
            "Full day — approx 10 hrs", 16000),
    "SOU": ("South Coast Waterfalls & Beach",
            "Seljalandsfoss Walk-Behind • Gljúfrabúi Hidden Falls • Skógafoss Rainbow • Reynisfjara Black Beach",
            "Full day — approx 10 hrs", 18000),
    "VAT": ("Jökulsárlón Glacier Lagoon",
            "Glacier Lagoon Boat Tour • Diamond Beach Ice Walk • Skaftafell Svartifoss Hike",
            "Full day — approx 10 hrs", 26000),
    "VES": ("Westman Islands Ferry Tour",
            "Ferry to Heimaey • Eldfell Volcano Hike • Lava Fields Walk • Puffin Coastal Walk",
            "Full day — approx 9 hrs", 22000),
    "LAK": ("Lakagígar Lava System",
            "F206 Highland Route • Laki Crater Row • Tjarnargígur Lava Lake • Eldgjá Gorge Drive",
            "Full day — approx 11 hrs", 30000),
    "KER": ("Kerlingarfjöll Hot Springs Trek",
            "Kerlingarfjöll Geothermal Trek • Hveradalir Hot Springs • Rhyolite Mountain Views",
            "Full day — approx 9 hrs", 25000),
    "HEK": ("Landmannalaugar Rainbow Hike",
            "Landmannalaugar Geothermal Pool • Rainbow Mountains Hike • Laugahraun Lava Field",
            "Full day — approx 11 hrs", 27000),
    "AUR": ("Northern Lights & Dark Sky",
            "Rural Dark Sky Zone Drive • Aurora Borealis Hunt • Varmahlíð Village • Glaumbaer Turf Farm",
            "Evening tour — 6 hrs | Best Oct–Mar", 19000),
    "PEN": ("Blue Lagoon & Reykjanes",
            "Blue Lagoon Geothermal Spa • Bridge Between Continents • Gunnuhver Hot Springs • Reykjanes Lighthouse",
            "Full day — approx 8 hrs", 21000),
    "THO": ("Þórsmörk Valley Trek",
            "Þórsmörk Glacier Valley • Stakkholtsgjá Canyon Hike • Fimmvörðuháls Trail Start",
            "Full day — approx 10 hrs", 28000),
    "HOL": ("Strandir Seal Watching",
            "Djúpavík Historic Village • Sorcery Museum Hólmavík • Seal Colony Coastline • Bjarnarfjörður Fjord",
            "Full day — approx 10 hrs", 20000),
    "ASK": ("Askja Caldera & Viti Crater",
            "F88 Highland Route • Askja Caldera Rim Walk • Viti Crater Lake • Öskjuvatn Lake Viewpoint",
            "Full day — approx 12 hrs", 32000),
    "GRM": ("Grímsey Arctic Circle Crossing",
            "Grímsey Island Flight • Arctic Circle Monument • Puffin Cliff Walk • Midnight Sun Experience",
            "Full day — approx 9 hrs", 35000),
    "HUS": ("Húsavík Whale Watching",
            "RIB Whale Watching Boat • Whale Museum Tour • Geosea Geothermal Sea Baths",
            "Full day — approx 8 hrs", 24000),
    "LAN": ("Fjallabak Rainbow Mountains",
            "Laugahraun Lava Field Walk • Natural Hot Spring Pool • Brennisteinsalda Volcano • Grænagil Canyon Hike",
            "Full day — approx 10 hrs", 26000),
    "FJA": ("Fjaðrárgljúfur Canyon Walk",
            "Fjaðrárgljúfur Canyon Trail • Kirkjubæjarklaustur Village • Systrafoss Waterfall • Kirkjugólf Basalt Floor",
            "Full day — approx 6 hrs", 14000),
    "SKA": ("Skaftafell Glacier Hike",
            "Svartifoss Waterfall Trail • Skaftafellsjökull Glacier View • Glacier Tongue Walk • Visitor Centre Exhibits",
            "Full day — approx 7 hrs", 18000),
    "BOR": ("Borgarfjörður Waterfalls",
            "Hraunfossar Lava Waterfalls • Barnafoss Bridge Falls • Deildartunguhver Hot Spring • Reykholt Historical Centre",
            "Full day — approx 8 hrs", 16000),
    "SGF": ("Siglufjörður Herring Era",
            "Herring Era Museum • Siglufjörður Harbour Walk • Héðinsfjörður Tunnel Drive • Ólafsfjörður Village",
            "Full day — approx 8 hrs", 17000),
    "DAL": ("Dalvík Sea Bathing & Whales",
            "Dalvík Swimming Lagoon • Arctic Sea Angling Tour • Böggvisstaðafjall Hike • Eyjafjörður Coast Drive",
            "Full day — approx 8 hrs", 19000),
    "FLA": ("Flatey Island Heritage Walk",
            "Flatey Village Walk • Medieval Church Visit • Bird Cliffs Trail • Breiðafjörður Ferry Cruise",
            "Full day — approx 9 hrs", 21000),
    "HVT": ("Hvítserkur Sea Stack & Seals",
            "Hvítserkur Rock Formation • Seal Colony Viewpoint • Vatnsnes Peninsula Drive • Illugastaðir Farm Walk",
            "Full day — approx 7 hrs", 15000),
    "DTF": ("Dettifoss Power & Canyon",
            "Dettifoss East Side View • Selfoss Upper Falls • Hljóðaklettar Echo Rocks • Ásbyrgi Horseshoe Canyon",
            "Full day — approx 9 hrs", 20000),
    "STF": ("Stöðvarfjörður & Petra's Stones",
            "Petra's Stone Collection • Stöðvarfjörður Harbour • Coastal Cliff Walk • Berufjörður Mountain Drive",
            "Full day — approx 6 hrs", 13000),
}

# ──────────────────────────────────────────────────────────────────────────────
# INCLUSIONS & EXCLUSIONS — shared across countries, INR pricing
# ──────────────────────────────────────────────────────────────────────────────

INCLUSIONS = {
    "Transport": [
        "Airport transfers in private AC vehicle",
        "All inter-city transfers as per itinerary",
        "Private coach transportation throughout",
    ],
    "Accommodation": [
        "4-star hotel accommodation with breakfast",
        "Boutique hotel stay in city centres",
    ],
    "Meals": [
        "Daily breakfast at hotel",
        "Welcome dinner on Day 1",
        "Farewell dinner at local restaurant",
    ],
    "Activities": [
        "All entrance fees as per itinerary",
        "Guided city walking tour",
        "Boat / cable car tickets as mentioned",
    ],
    "Extras": [
        "Dedicated English-speaking tour guide",
        "24/7 helpline support",
        "Comprehensive travel insurance",
    ],
}

EXCLUSIONS = {
    "Personal": [
        "Personal expenses and shopping",
        "Tips and gratuities for guides / drivers",
        "Camera / video fees at monuments",
    ],
    "Meals": [
        "Lunches and dinners (unless specified)",
        "Alcoholic beverages and soft drinks",
        "Room service charges",
    ],
    "Travel": [
        "International airfare",
        "Visa fees and processing charges",
        "Travel insurance (if not opted)",
    ],
    "Optional": [
        "Optional excursions not in itinerary",
        "Gondola / hot-air balloon rides",
        "Spa and wellness services",
    ],
}

# ──────────────────────────────────────────────────────────────────────────────
# HOTEL DATA — ~20 per country  (region_code, name, stars, city, price_notes)
# ──────────────────────────────────────────────────────────────────────────────

CH_HOTELS = [
    ("ZUR", "Hotel Schweizerhof Zurich", 5, "Zurich", "₹28,000/night"),
    ("ZUR", "25hours Langstrasse Zurich", 4, "Zurich", "₹18,000/night"),
    ("ZUR", "Hotel Felix Zurich", 3, "Zurich", "₹11,000/night"),
    ("LUC", "Hotel des Balances Lucerne", 4, "Lucerne", "₹22,000/night"),
    ("LUC", "Grand Hotel National Lucerne", 5, "Lucerne", "₹32,000/night"),
    ("BER", "Hotel Schweizerhof Bern", 5, "Bern", "₹30,000/night"),
    ("BER", "Hotel Bern", 3, "Bern", "₹12,000/night"),
    ("INT", "Victoria-Jungfrau Grand Hotel", 5, "Interlaken", "₹35,000/night"),
    ("INT", "Hotel Chalet Swiss", 3, "Interlaken", "₹10,000/night"),
    ("GEN", "Hotel Beau-Rivage Geneva", 5, "Geneva", "₹34,000/night"),
    ("GEN", "Hotel de la Paix Geneva", 4, "Geneva", "₹24,000/night"),
    ("ZER", "Grand Hotel Zermatterhof", 5, "Zermatt", "₹38,000/night"),
    ("ZER", "Hotel Pollux Zermatt", 3, "Zermatt", "₹14,000/night"),
    ("MON", "Fairmont Le Montreux Palace", 5, "Montreux", "₹36,000/night"),
    ("BAS", "Grand Hotel Les Trois Rois", 5, "Basel", "₹33,000/night"),
    ("LUG", "Hotel Splendide Royal Lugano", 5, "Lugano", "₹29,000/night"),
    ("ENG", "Badrutt's Palace Hotel", 5, "St. Moritz", "₹45,000/night"),
    ("GRD", "Hotel Belvedere Grindelwald", 4, "Grindelwald", "₹20,000/night"),
    ("DAV", "Hotel Seehof Davos", 4, "Davos", "₹18,000/night"),
    ("LAT", "Hotel Staubbach Lauterbrunnen", 3, "Lauterbrunnen", "₹9,500/night"),
]

IS_HOTELS = [
    ("REY", "Hotel Borg Reykjavik", 4, "Reykjavik", "₹22,000/night"),
    ("REY", "Canopy by Hilton Reykjavik", 4, "Reykjavik", "₹19,000/night"),
    ("REY", "Kex Hostel Reykjavik", 3, "Reykjavik", "₹8,000/night"),
    ("NOR", "Hotel Kea Akureyri", 4, "Akureyri", "₹18,000/night"),
    ("NOR", "Icelandair Hotel Akureyri", 3, "Akureyri", "₹14,000/night"),
    ("SOU", "Hotel Rangá", 4, "Hella", "₹24,000/night"),
    ("SOU", "Hotel Katla Vík", 3, "Vík", "₹12,000/night"),
    ("GCR", "Ion Adventure Hotel", 4, "Selfoss", "₹26,000/night"),
    ("GCR", "Hotel Geysir", 3, "Geysir", "₹11,000/night"),
    ("HUS", "Fosshotel Húsavík", 3, "Húsavík", "₹13,000/night"),
    ("EAS", "Fosshotel Eastfjords", 3, "Djúpivogur", "₹11,000/night"),
    ("DIA", "Fosshotel Mývatn", 3, "Mývatn", "₹13,000/night"),
    ("VAT", "Fosshotel Glacier Lagoon", 4, "Höfn", "₹20,000/night"),
    ("WFJ", "Hotel Ísafjörður", 3, "Ísafjörður", "₹14,000/night"),
    ("PEN", "Blue Lagoon Retreat Hotel", 5, "Grindavík", "₹42,000/night"),
    ("SNA", "Hotel Búðir", 4, "Búðir", "₹22,000/night"),
    ("BOR", "Hotel Húsafell", 4, "Húsafell", "₹20,000/night"),
    ("SGF", "Sigló Hotel Siglufjörður", 4, "Siglufjörður", "₹18,000/night"),
    ("VES", "Hotel Vestmannaeyjar", 3, "Heimaey", "₹13,000/night"),
    ("SKA", "Fosshotel Skaftafell", 3, "Skaftafell", "₹12,000/night"),
]


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _code():
    return "IT-" + str(secrets.randbelow(900000) + 100000)


def _dt_code(prefix):
    return f"DT-{prefix}-{secrets.randbelow(9000) + 1000}"


def _ie_code(prefix):
    return f"IE-{prefix}-{secrets.randbelow(9000) + 1000}"


# ──────────────────────────────────────────────────────────────────────────────
# MANAGEMENT COMMAND
# ──────────────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Seed Switzerland & Iceland demo data (30 regions each, INR currency, varied plans)"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Clear all seeded data before re-seeding")

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear()

        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stderr.write("No superuser found. Create one first: python manage.py createsuperuser")
            return

        with transaction.atomic():
            ch = self._country("Switzerland", "CHE")
            is_ = self._country("Iceland", "ISL")

            cats = self._categories()
            ch_incl, ch_excl = self._inclusions(ch, cats)
            is_incl, is_excl = self._inclusions(is_, cats)

            self._regions_tours_templates(ch, SWITZERLAND_REGIONS, CH_TOURS, admin, ch_incl, ch_excl)
            self._regions_tours_templates(is_, ICELAND_REGIONS, IS_TOURS, admin, is_incl, is_excl)

            self._hotels(ch, SWITZERLAND_REGIONS, CH_HOTELS)
            self._hotels(is_, ICELAND_REGIONS, IS_HOTELS)

        self.stdout.write(self.style.SUCCESS(
            "\nDone!  Switzerland + Iceland | 30 regions each | "
            "60 day tours | 180 templates (Solo/Couple/Group) | "
            "inclusions & exclusions | ~40 hotels | INR currency\n"
        ))

    # ── CLEAR ───────────────────────────────────────────────────────────────

    def _clear(self):
        self.stdout.write("  Clearing old data ...")
        for code in ("CHE", "ISL"):
            qs = Country.objects.filter(code=code)
            if not qs.exists():
                continue
            country = qs.first()

            # delete in dependency order
            tmpl_ids = ItineraryTemplate.objects.filter(country=country).values_list("id", flat=True)
            ItineraryTemplateInclExcl.objects.filter(template_id__in=tmpl_ids).delete()
            ItineraryTemplateDay.objects.filter(template_id__in=tmpl_ids).delete()
            ItineraryTemplate.objects.filter(country=country).delete()

            InclusionExclusion.objects.filter(country=country).delete()

            region_ids = Region.objects.filter(country=country).values_list("id", flat=True)
            Hotel.objects.filter(region_id__in=region_ids).delete()
            DayTourAttraction.objects.filter(day_tour__region_id__in=region_ids).delete()
            DayTour.objects.filter(region_id__in=region_ids).delete()
            Attraction.objects.filter(region_id__in=region_ids).delete()
            Region.objects.filter(country=country).delete()
            qs.delete()
        self.stdout.write("  Cleared.")

    # ── COUNTRY ─────────────────────────────────────────────────────────────

    def _country(self, name, code):
        obj, created = Country.objects.get_or_create(
            code=code, defaults={"name": name, "iso_code": code, "is_active": True}
        )
        self.stdout.write(f"  {'Created' if created else 'Found'} country: {name}")
        return obj

    # ── CATEGORIES ──────────────────────────────────────────────────────────

    def _categories(self):
        cats = {}
        all_names = list(INCLUSIONS.keys()) + [k for k in EXCLUSIONS if k not in INCLUSIONS]
        for name in all_names:
            cat, _ = InclExclCategory.objects.get_or_create(name=name, defaults={"is_active": True})
            cats[name] = cat
        return cats

    # ── INCLUSIONS / EXCLUSIONS ─────────────────────────────────────────────

    def _inclusions(self, country, cats):
        incl_objs, excl_objs = [], []
        for cat_name, items in INCLUSIONS.items():
            cat = cats[cat_name]
            for text in items:
                ie, _ = InclusionExclusion.objects.get_or_create(
                    country=country, item_service=text,
                    defaults={
                        "unique_code": _ie_code(country.code),
                        "type": "INCLUSION",
                        "category": cat,
                        "is_active": True,
                    },
                )
                incl_objs.append(ie)

        for cat_name, items in EXCLUSIONS.items():
            cat, _ = InclExclCategory.objects.get_or_create(name=cat_name, defaults={"is_active": True})
            for text in items:
                ie, _ = InclusionExclusion.objects.get_or_create(
                    country=country, item_service=text,
                    defaults={
                        "unique_code": _ie_code(country.code),
                        "type": "EXCLUSION",
                        "category": cat,
                        "is_active": True,
                    },
                )
                excl_objs.append(ie)
        self.stdout.write(
            f"  Inclusions/Exclusions for {country.name}: {len(incl_objs)} incl, {len(excl_objs)} excl"
        )
        return incl_objs, excl_objs

    # ── REGIONS + TOURS + TEMPLATES ─────────────────────────────────────────

    def _regions_tours_templates(self, country, regions_data, tours_data, admin, incl_list, excl_list):
        for i, (code, name, desc) in enumerate(regions_data):
            region_code = f"{country.code[:2]}{code}"[:10]
            region, _ = Region.objects.get_or_create(
                country=country, name=name,
                defaults={"code": region_code, "description": desc, "display_order": i + 1, "is_active": True},
            )

            # day tour
            tour_info = tours_data.get(code)
            if tour_info:
                tour_name, activity, timing, price = tour_info
            else:
                tour_name = f"{name} Highlights"
                activity = f"{name} Scenic Walk"
                timing = "Full day — approx 7 hrs"
                price = 15000

            day_tour = self._day_tour(
                region=region,
                activity=activity,
                code=_dt_code(code),
                text=(
                    f"{timing}\n\nExplore {name} on this immersive day tour. "
                    f"Your expert guide shares local stories and insider tips."
                ),
                timing=timing,
                price=price,
            )

            # parse activity bullets into attractions
            for idx, attr_name in enumerate(a.strip() for a in activity.split("•") if a.strip()):
                attr, _ = Attraction.objects.get_or_create(
                    region=region, name=attr_name[:200],
                    defaults={
                        "reference_no": f"ATT-{region.code}-{idx + 1}-{secrets.randbelow(9000) + 1000}",
                        "key_features_notes": f"A major highlight of {name}.",
                        "is_active": True,
                    },
                )
                DayTourAttraction.objects.get_or_create(
                    day_tour=day_tour, attraction=attr,
                    defaults={"visit_order": idx + 1},
                )

            # ── 3 templates per region ──────────────────────────────────

            # 1) Solo Day Tour (default)
            if not ItineraryTemplate.objects.filter(region=region, is_default=True).exists():
                t1, _ = ItineraryTemplate.objects.get_or_create(
                    region=region, name=f"{name} — Solo Day Tour",
                    defaults={
                        "country": country, "code": _code(),
                        "includes_night": False, "is_default": True,
                        "travel_type": "SOLO", "is_active": True,
                        "description": f"Solo day exploration of {name}. Perfect for independent travellers.",
                        "created_by": admin,
                    },
                )
                self._attach(t1, day_tour, incl_list, excl_list)

            # 2) Couple Day & Night
            t2, created = ItineraryTemplate.objects.get_or_create(
                region=region, name=f"{name} — Couple Day & Night",
                defaults={
                    "country": country, "code": _code(),
                    "includes_night": True, "is_default": False,
                    "travel_type": "COUPLE", "is_active": True,
                    "description": f"Romantic day + overnight stay in {name}. Includes evening leisure time.",
                    "created_by": admin,
                },
            )
            if created:
                self._attach(t2, day_tour, incl_list, excl_list)

            # 3) Group Day Tour
            t3, created = ItineraryTemplate.objects.get_or_create(
                region=region, name=f"{name} — Group Day Tour",
                defaults={
                    "country": country, "code": _code(),
                    "includes_night": False, "is_default": False,
                    "travel_type": "GROUP", "is_active": True,
                    "description": f"Group day tour of {name}. Ideal for families and friends travelling together.",
                    "created_by": admin,
                },
            )
            if created:
                self._attach(t3, day_tour, incl_list, excl_list)

            self.stdout.write(f"    {name} — tour + 3 templates")

    # ── HOTELS ──────────────────────────────────────────────────────────────

    def _hotels(self, country, regions_data, hotels_data):
        region_map = {}
        for code, name, _ in regions_data:
            region = Region.objects.filter(country=country, name=name).first()
            if region:
                region_map[code] = region

        count = 0
        for rcode, hotel_name, stars, city, pnotes in hotels_data:
            region = region_map.get(rcode)
            if not region:
                continue
            Hotel.objects.get_or_create(
                name=hotel_name, country=country,
                defaults={
                    "region": region, "star_rating": stars, "city": city,
                    "price_notes": pnotes, "is_active": True,
                    "display_order": count,
                },
            )
            count += 1
        self.stdout.write(f"  Hotels for {country.name}: {count}")

    # ── DAY TOUR (raw SQL for legacy NOT NULL columns) ──────────────────────

    def _day_tour(self, region, activity, code, text, timing, price):
        existing = DayTour.objects.filter(region=region, activity_combination=activity).first()
        if existing:
            return existing

        from django.utils import timezone

        now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO day_tours (
                    unique_code, region_id, activity_combination,
                    itinerary_text, est_time_distance,
                    display_order, is_active, currency, price,
                    includes_night, is_default,
                    created_at, updated_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                [
                    code, region.id, activity,
                    text, timing.split("\n")[0],
                    0, True, "INR", price,
                    False, False,
                    now, now,
                ],
            )
            tour_id = cursor.lastrowid
        return DayTour.objects.get(id=tour_id)

    # ── ATTACH DAY/INCL-EXCL TO TEMPLATE ────────────────────────────────────

    def _attach(self, template, day_tour, incl_list, excl_list):
        ItineraryTemplateDay.objects.get_or_create(
            template=template, day_number=1, defaults={"day_tour": day_tour}
        )
        for ie in incl_list:
            ItineraryTemplateInclExcl.objects.get_or_create(template=template, incl_excl=ie)
        for ie in excl_list:
            ItineraryTemplateInclExcl.objects.get_or_create(template=template, incl_excl=ie)
