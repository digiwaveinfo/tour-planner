from django.contrib import admin
from .models import ItineraryTemplate,ItineraryTemplateDay,ItineraryTemplateInclExcl

@admin.register(ItineraryTemplate)
class ItineraryTemplateAdmin(admin.ModelAdmin):
 list_display=("id","name","country","total_nights","total_days","is_active")
 search_fields=("name","code","country__name")
 list_filter=("country","is_active")
 ordering=("country","name")
 autocomplete_fields=("country","created_by")
 readonly_fields=("created_at","updated_at","deleted_at")

@admin.register(ItineraryTemplateDay)
class ItineraryTemplateDayAdmin(admin.ModelAdmin):
 list_display=("id","template","day_number","day_tour","is_arrival_day","is_departure_day")
 search_fields=("template__name","day_tour__unique_code")
 list_filter=("template","is_arrival_day","is_departure_day")
 ordering=("template","day_number")
 autocomplete_fields=("template","day_tour")

@admin.register(ItineraryTemplateInclExcl)
class ItineraryTemplateInclExclAdmin(admin.ModelAdmin):
 list_display=("id","template","incl_excl")
 search_fields=("template__name","incl_excl__unique_code","incl_excl__item_service")
 list_filter=("template",)
 autocomplete_fields=("template","incl_excl")