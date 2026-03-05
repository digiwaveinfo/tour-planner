from django.contrib import admin
from .models import Country,Region,CountryImage,RegionImage
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin

class CountryResource(resources.ModelResource):
    class Meta:
        model = Country
        import_id_fields = ("code",)   
        fields = ("name", "code", "iso_code", "is_active")
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        if row.get("name"):
            row["name"] = row["name"].strip()
        if row.get("code"):
            row["code"] = row["code"].upper()
        if row.get("iso_code"):
            row["iso_code"] = row["iso_code"].upper()

class CountryImageInline(admin.TabularInline):
    model = CountryImage
    extra = 1

@admin.register(Country)
class CountryAdmin(ImportExportModelAdmin):
 resource_class = CountryResource
 list_display=("id","name","code","iso_code","is_active","created_at")
 search_fields=("name","code","iso_code")
 list_filter=("is_active",)
 ordering=("name",)
 readonly_fields=("created_at","updated_at","deleted_at")
 inlines = [CountryImageInline]

class RegionResource(resources.ModelResource):
    country_code = fields.Field(column_name="country_code",attribute="country",widget=ForeignKeyWidget(Country, "code"))

    class Meta:
        model = Region
        import_id_fields = ("code",)   
        fields = ("country_code","name","code","description","display_order",)
        skip_unchanged = True
        report_skipped = True
    def before_import_row(self, row, **kwargs):
        if row.get("country_code"):
            row["country_code"] = row["country_code"].upper().strip()
        if row.get("code"):
            row["code"] = row["code"].upper().strip()
        if row.get("name"):
            row["name"] = row["name"].strip()

class RegionImageInline(admin.TabularInline):
    model = RegionImage
    extra = 1

@admin.register(Region)
class RegionAdmin(ImportExportModelAdmin):
 resource_class = RegionResource
 list_display=("id","name","code","country","description","display_order","is_active")
 search_fields=("name","code","country__name")
 list_filter=("country","is_active")
 ordering=("country","display_order","name")
 autocomplete_fields=("country",)
 readonly_fields=("created_at","updated_at","deleted_at")
 inlines = [RegionImageInline]