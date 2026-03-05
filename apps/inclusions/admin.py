from django.contrib import admin
from .models import InclExclCategory,InclusionExclusion
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from apps.geography.models import Country
from import_export.admin import ImportExportModelAdmin

class InclExclCategoryResource(resources.ModelResource):
    class Meta:
        model = InclExclCategory
        import_id_fields = ("name",)
        fields = ("name","display_order","is_active")
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        if row.get("name"):
            row["name"] = row["name"].strip()

@admin.register(InclExclCategory)
class InclExclCategoryAdmin(ImportExportModelAdmin):
 resource_class = InclExclCategoryResource
 list_display=("id","name","display_order","is_active")
 search_fields=("name",)
 list_filter=("is_active",)
 ordering=("display_order","name")

class InclusionExclusionResource(resources.ModelResource):
    country_code = fields.Field(column_name="country_code",attribute="country",widget=ForeignKeyWidget(Country, "code"))
    category_name = fields.Field(column_name="category_name",attribute="category",widget=ForeignKeyWidget(InclExclCategory, "name"))

    class Meta:
        model = InclusionExclusion
        fields = ("country_code","type","category_name","item_service","details_notes","source_files","display_order",)
        exclude = ("id", "unique_code", "created_at", "updated_at", "deleted_at")
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ()

@admin.register(InclusionExclusion)
class InclusionExclusionAdmin(ImportExportModelAdmin):
 resource_class = InclusionExclusionResource
 list_display=("id","unique_code","type","item_service","country","category","display_order","is_active")
 search_fields=("unique_code","item_service","country__name","category__name")
 list_filter=("type","country","category","is_active")
 ordering=("country","display_order","item_service")
 autocomplete_fields=("country","category")
 readonly_fields=("unique_code","created_at","updated_at","deleted_at")