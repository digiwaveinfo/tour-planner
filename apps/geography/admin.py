from django.contrib import admin
from .models import Country,Region

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
 list_display=("id","name","code","iso_code","is_active","created_at")
 search_fields=("name","code","iso_code")
 list_filter=("is_active",)
 ordering=("name",)
 readonly_fields=("created_at","updated_at","deleted_at")

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
 list_display=("id","name","code","country","display_order","is_active")
 search_fields=("name","code","country__name")
 list_filter=("country","is_active")
 ordering=("country","display_order","name")
 autocomplete_fields=("country",)
 readonly_fields=("created_at","updated_at","deleted_at")