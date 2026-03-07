from django.contrib import admin
from .models import ItineraryTemplate, ItineraryTemplateDay, ItineraryTemplateInclExcl


class ItineraryTemplateDayInline(admin.TabularInline):
    """
    Inline for managing the single day-tour linked to a template.
    Shown directly on the template edit page — no separate 'Manage Days' required.
    """
    model = ItineraryTemplateDay
    extra = 1
    max_num = 1  # Each template is always 1 day
    autocomplete_fields = ("day_tour",)
    fields = ("day_number", "day_tour", "custom_notes", "is_arrival_day", "is_departure_day")
    verbose_name = "Day Tour (Activity for this day)"
    verbose_name_plural = "Day Tour"


class ItineraryTemplateInclExclInline(admin.TabularInline):
    model = ItineraryTemplateInclExcl
    extra = 0
    autocomplete_fields = ("incl_excl",)


@admin.register(ItineraryTemplate)
class ItineraryTemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "country", "region", "includes_night", "total_days", "total_nights", "travel_type", "is_default", "is_active")
    search_fields = ("name", "code", "country__name", "region__name")
    list_filter = ("country", "region", "includes_night", "is_default", "is_active", "travel_type")
    ordering = ("country", "region", "name")
    autocomplete_fields = ("country", "region", "created_by")
    readonly_fields = ("code", "total_days", "total_nights", "created_at", "updated_at", "deleted_at")
    # Day management merged into the template form via inline
    inlines = [ItineraryTemplateDayInline, ItineraryTemplateInclExclInline]
    fieldsets = (
        ("Basic Info", {
            "fields": ("country", "region", "name", "code", "description", "travel_type")
        }),
        ("Template Type", {
            "fields": ("includes_night", "total_days", "total_nights"),
            "description": "Select 'Includes Night' to make this a 1 Day + 1 Night template. Total Days/Nights are set automatically.",
        }),
        ("Settings", {
            "fields": ("is_default", "is_active", "created_by")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at", "deleted_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(ItineraryTemplateDay)
class ItineraryTemplateDayAdmin(admin.ModelAdmin):
    list_display = ("id", "template", "day_number", "day_tour", "is_arrival_day", "is_departure_day")
    search_fields = ("template__name", "day_tour__unique_code")
    list_filter = ("template", "is_arrival_day", "is_departure_day")
    ordering = ("template", "day_number")
    autocomplete_fields = ("template", "day_tour")


@admin.register(ItineraryTemplateInclExcl)
class ItineraryTemplateInclExclAdmin(admin.ModelAdmin):
    list_display = ("id", "template", "incl_excl")
    search_fields = ("template__name", "incl_excl__unique_code", "incl_excl__item_service")
    list_filter = ("template",)
    autocomplete_fields = ("template", "incl_excl")