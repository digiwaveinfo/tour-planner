from django.contrib import admin
from .models import DayTour,DayTourAttraction

@admin.register(DayTour)
class DayTourAdmin(admin.ModelAdmin):
 list_display=("id","unique_code","region","overnight_location","display_order","is_active")
 search_fields=("unique_code","activity_combination","region__name","overnight_location")
 list_filter=("region","is_active","overnight_location")
 ordering=("region","display_order")
 autocomplete_fields=("region","created_by")
 readonly_fields=("created_at","updated_at","deleted_at")

@admin.register(DayTourAttraction)
class DayTourAttractionAdmin(admin.ModelAdmin):
 list_display=("id","day_tour","attraction","visit_order")
 search_fields=("day_tour__unique_code","attraction__name")
 list_filter=("day_tour",)
 ordering=("day_tour","visit_order")
 autocomplete_fields=("day_tour","attraction")