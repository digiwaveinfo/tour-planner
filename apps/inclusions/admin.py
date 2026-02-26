from django.contrib import admin
from .models import InclExclCategory,InclusionExclusion

@admin.register(InclExclCategory)
class InclExclCategoryAdmin(admin.ModelAdmin):
 list_display=("id","name","display_order","is_active")
 search_fields=("name",)
 list_filter=("is_active",)
 ordering=("display_order","name")

@admin.register(InclusionExclusion)
class InclusionExclusionAdmin(admin.ModelAdmin):
 list_display=("id","unique_code","type","item_service","country","category","display_order","is_active")
 search_fields=("unique_code","item_service","country__name","category__name")
 list_filter=("type","country","category","is_active")
 ordering=("country","display_order","item_service")
 autocomplete_fields=("country","category")
 readonly_fields=("created_at","updated_at","deleted_at")