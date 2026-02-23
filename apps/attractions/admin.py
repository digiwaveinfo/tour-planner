from django.contrib import admin
from .models import Attraction

@admin.register(Attraction)
class AttractionAdmin(admin.ModelAdmin):
 list_display=("id","reference_no","name","region","display_order","is_active")
 search_fields=("reference_no","name","region__name")
 list_filter=("region","is_active")
 ordering=("region","display_order","name")
 autocomplete_fields=("region",)
 readonly_fields=("created_at","updated_at","deleted_at")