from django.contrib import admin
from .models import ItineraryTemplate,ItineraryTemplateDay,ItineraryTemplateInclExcl
from import_export import resources
from import_export.widgets import ForeignKeyWidget
from import_export import fields
from apps.geography.models import Country
from import_export.admin import ImportExportModelAdmin
from apps.day_tours.models import DayTour
from apps.inclusions.models import InclusionExclusion

class CountryWidget(ForeignKeyWidget):
    def get_queryset(self, value, row, *args, **kwargs):
        return self.model.objects.filter(code__iexact=value)

class TemplateWidget(ForeignKeyWidget):
    def get_queryset(self, value, row, *args, **kwargs):
        return self.model.objects.filter(code__iexact=value)

class DayTourWidget(ForeignKeyWidget):
    def get_queryset(self, value, row, *args, **kwargs):
        return self.model.objects.filter(unique_code__iexact=value)

class InclExclWidget(ForeignKeyWidget):
    def get_queryset(self,value,row,*args,**kwargs):
        return self.model.objects.filter(unique_code__iexact=value)

class ItineraryTemplateResource(resources.ModelResource):
    country_code = fields.Field(column_name="country_code",attribute="country",widget=CountryWidget(Country, "code"),)

    class Meta:
        model = ItineraryTemplate
        fields = ("country_code","name","total_nights","total_days","description","is_default","is_active",)
        exclude = ("id", "code", "created_at", "updated_at", "deleted_at")
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ("name",)

@admin.register(ItineraryTemplate)
class ItineraryTemplateAdmin(ImportExportModelAdmin):
 resource_class = ItineraryTemplateResource
 list_display=("id","code","name","country","total_nights","total_days","is_active")
 search_fields=("name","code","country__name")
 list_filter=("country","is_active","travel_type")
 ordering=("country","name")
 autocomplete_fields=("country","created_by")
 readonly_fields=("created_at","updated_at","deleted_at")

class ItineraryTemplateDayResource(resources.ModelResource):
    template_code = fields.Field(column_name="template_code",attribute="template",widget=TemplateWidget(ItineraryTemplate, "code"),)
    day_tour_code = fields.Field(column_name="day_tour_code",attribute="day_tour",widget=DayTourWidget(DayTour, "unique_code"),)

    class Meta:
        model = ItineraryTemplateDay
        fields = ("template_code","day_number","day_tour_code","custom_notes","is_arrival_day","is_departure_day","display_order",)
        exclude = ("id",)
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ("template_code","day_number")

@admin.register(ItineraryTemplateDay)
class ItineraryTemplateDayAdmin(ImportExportModelAdmin):
 resource_class = ItineraryTemplateDayResource
 list_display=("id","template","day_number","day_tour","is_arrival_day","is_departure_day")
 search_fields=("template__name","day_tour__unique_code")
 list_filter=("template","is_arrival_day","is_departure_day")
 ordering=("template","day_number")
 autocomplete_fields=("template","day_tour")


class ItineraryTemplateInclExclResource(resources.ModelResource):
    template_code=fields.Field(column_name="template_code",attribute="template",widget=TemplateWidget(ItineraryTemplate,"code"))
    incl_excl_code=fields.Field(column_name="incl_excl_code",attribute="incl_excl",widget=InclExclWidget(InclusionExclusion,"unique_code"))

    class Meta:
        model=ItineraryTemplateInclExcl
        fields=("template_code","incl_excl_code")
        exclude=("id",)
        skip_unchanged=True
        report_skipped=True
        import_id_fields=("template_code","incl_excl_code")
        
@admin.register(ItineraryTemplateInclExcl)
class ItineraryTemplateInclExclAdmin(ImportExportModelAdmin):
 resource_class=ItineraryTemplateInclExclResource
 list_display=("id","template","incl_excl")
 search_fields=("template__name","incl_excl__unique_code","incl_excl__item_service")
 list_filter=("template",)
 autocomplete_fields=("template","incl_excl")