from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from apps.geography.models import Country, Region
from .models import Hotel, HotelImage
import json

class HotelResource(resources.ModelResource):
    country_code = fields.Field(column_name="country_code",attribute="country",widget=ForeignKeyWidget(Country, "code"))
    region = fields.Field(column_name="region",attribute="region",widget=ForeignKeyWidget(Region, "name"))

    class Meta:
        model = Hotel
        import_id_fields = ("name",)
        fields = (
            "country_code", "region", "name", "city", "address", 
            "star_rating", "hotel_type", "description", "contact_phone", 
            "contact_email", "website", "check_in_time", "check_out_time", 
            "latitude", "longitude", "amenities", "price_notes", "display_order",)
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
            if row.get("region"):
                row["region"] = row["region"].strip()
            if row.get("name"):
                row["name"] = row["name"].strip()
            if row.get("amenities"):
                amenities = [
                    a.strip() for a in str(row["amenities"]).split(",") if a.strip()
                ]
                row["amenities"] = json.dumps(amenities)

class HotelImageInline(admin.TabularInline):
    model = HotelImage
    extra = 1

@admin.register(Hotel)
class HotelAdmin(ImportExportModelAdmin):
    resource_class = HotelResource
    list_display = ("id", "name", "country", "region", "city", "star_rating", "is_active")
    search_fields = ("name", "city", "region__name", "country__name")
    list_filter = ("country", "region", "star_rating", "is_active")
    ordering = ("country", "region", "name")
    autocomplete_fields = ("country", "region")
    readonly_fields = ("created_at", "updated_at", "deleted_at")
    inlines = [HotelImageInline]