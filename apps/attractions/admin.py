from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from apps.geography.models import Region
from django.contrib import admin
from .models import Attraction,AttractionImage

class AttractionResource(resources.ModelResource):
    region = fields.Field(column_name="region",attribute="region",widget=ForeignKeyWidget(Region, "name"))
    name = fields.Field(column_name="name",attribute="name")

    class Meta:
        model = Attraction
        import_id_fields = ("region","name")
        fields = ("region","name","key_features_notes","source_citations","latitude","longitude","display_order",)
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        if row.get("region"):
            row["region"] = row["region"].strip()
        if row.get("name"):
            row["name"] = row["name"].strip()

class AttractionImageInline(admin.TabularInline):
    model = AttractionImage
    extra = 1

@admin.register(Attraction)
class AttractionAdmin(ImportExportModelAdmin):
 resource_class = AttractionResource
 list_display=("id","reference_no","name","region","display_order","is_active")
 inlines = [AttractionImageInline]
 search_fields=("reference_no","name","region__name")
 list_filter=("region","is_active")
 ordering=("region","display_order","name")
 autocomplete_fields=("region",)
 readonly_fields=("reference_no","created_at","updated_at","deleted_at")
