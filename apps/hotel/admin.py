from django.contrib import admin
from .models import Hotel

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
 list_display=("id","name","country","region","city","star_rating","is_active")
 search_fields=("name","city","region__name","country__name")
 list_filter=("country","region","star_rating","is_active")
 ordering=("country","region","name")
 autocomplete_fields=("country","region")
 readonly_fields=("created_at","updated_at","deleted_at")