from django.contrib import admin
from .models import DayTour,DayTourAttraction
from apps.geography.models import Region
from apps.attractions.models import Attraction
from import_export import resources,fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin

class RegionWidget(ForeignKeyWidget):
    def get_queryset(self,value,row,*args,**kwargs):
        return self.model.objects.filter(name__iexact=value)

class AttractionWidget(ForeignKeyWidget):
    def get_queryset(self,value,row,*args,**kwargs):
        return self.model.objects.filter(reference_no__iexact=str(value).strip())

class DayTourWidget(ForeignKeyWidget):
    def get_queryset(self,value,row,*args,**kwargs):
        return self.model.objects.filter(unique_code__iexact=str(value).strip())

class DayTourResource(resources.ModelResource):
    region=fields.Field(column_name="region",attribute="region",widget=RegionWidget(Region,"name"))
    class Meta:
        model=DayTour
        fields=("region","travel_type","validity_mode","valid_from","valid_to","price","currency","activity_combination","est_time_distance","overnight_location","source_file","itinerary_text","display_order","is_active")
        exclude=("id","unique_code","created_at","updated_at","deleted_at")
        skip_unchanged=True
        report_skipped=True
        import_id_fields=()
    def before_import_row(self,row,**kwargs):
        if row.get("valid_from")=="":
            row["valid_from"]=None
        if row.get("valid_to")=="":
            row["valid_to"]=None

@admin.register(DayTour)
class DayTourAdmin(ImportExportModelAdmin):
    resource_class=DayTourResource
    list_display=("id","unique_code","region","overnight_location","display_order","is_active")
    search_fields=("unique_code","activity_combination","region__name","overnight_location")
    list_filter=("region","is_active","overnight_location")
    ordering=("region","display_order")
    autocomplete_fields=("region","created_by")
    readonly_fields=("created_at","updated_at","deleted_at")

class DayTourAttractionResource(resources.ModelResource):
    day_tour_code=fields.Field(column_name="day_tour_code",attribute="day_tour",widget=DayTourWidget(DayTour,"unique_code"))
    attraction_reference_no=fields.Field(column_name="attraction_reference_no",attribute="attraction",widget=AttractionWidget(Attraction,"reference_no"))
    class Meta:
        model=DayTourAttraction
        fields=("day_tour_code","attraction_reference_no","visit_order")
        exclude=("id",)
        skip_unchanged=True
        report_skipped=True
        import_id_fields = ("day_tour_code", "attraction_reference_no")

@admin.register(DayTourAttraction)
class DayTourAttractionAdmin(ImportExportModelAdmin):
    resource_class=DayTourAttractionResource
    list_display=("id","day_tour","attraction","visit_order")
    search_fields=("day_tour__unique_code","attraction__name")
    list_filter=("day_tour",)
    ordering=("day_tour","visit_order")
    autocomplete_fields=("day_tour","attraction")