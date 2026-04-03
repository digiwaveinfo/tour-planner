from rest_framework import serializers
from apps.itinerary_templates.models import *
from apps.day_tours.serializer import DayTourSerializer

class ItineraryTemplateDaySerializer(serializers.ModelSerializer):
    morning_tour_detail = DayTourSerializer(source="morning_tour", read_only=True)
    noon_tour_detail = DayTourSerializer(source="noon_tour", read_only=True)
    night_tour_detail = DayTourSerializer(source="night_tour", read_only=True)

    class Meta:
        model = ItineraryTemplateDay
        fields = "__all__"
        extra_kwargs = {
            'template': {'required': False, 'allow_null': True},
        }

    def validate(self, data):
      # No cross-field validation needed for single-day templates
      return data

class ItineraryTemplateInclExclSerializer(serializers.ModelSerializer):
    item_text=serializers.CharField(source="incl_excl.item_service",read_only=True)
    type=serializers.CharField(source="incl_excl.type",read_only=True)
    category_name=serializers.CharField(source="incl_excl.category.name",read_only=True)
    class Meta:
        model = ItineraryTemplateInclExcl
        fields = "__all__"

class ItineraryTemplateSerializer(serializers.ModelSerializer):
 days = ItineraryTemplateDaySerializer(many=True, read_only=True)
 incl_excl = ItineraryTemplateInclExclSerializer(many=True, read_only=True)
 country_name = serializers.CharField(source="country.name", read_only=True)
 region_name = serializers.CharField(source="region.name", read_only=True, default=None)
 class Meta:
  model=ItineraryTemplate
  fields="__all__"
  read_only_fields=("created_by","created_at","updated_at","deleted_at","code","total_days","total_nights")