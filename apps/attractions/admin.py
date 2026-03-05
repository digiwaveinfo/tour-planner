from import_export.admin import ImportExportModelAdmin
from import_export import resources
from django.contrib import admin
from .models import Attraction,AttractionImage

class AttractionResource(resources.ModelResource):
    class Meta:
        model = Attraction
        import_id_fields = ('reference_no',)
        fields = ('reference_no', 'region', 'name', 'latitude', 'longitude')

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
 readonly_fields=("created_at","updated_at","deleted_at")
