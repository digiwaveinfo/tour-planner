from rest_framework import serializers
from apps.itinerary_templates.models import *
from apps.day_tours.serializer import DayTourSerializer

class ItineraryTemplateDaySerializer(serializers.ModelSerializer):
    day_tour_detail = DayTourSerializer(source="day_tour", read_only=True)

    class Meta:
        model = ItineraryTemplateDay
        fields = "__all__"
        extra_kwargs = {
            'template': {'required': False},
        }

    def validate(self, data):
      template = data.get("template") or getattr(self.instance, "template", None)
      day_number = data.get("day_number") or getattr(self.instance, "day_number", None)
      if template and day_number:
          if day_number > template.total_days:
              raise serializers.ValidationError(
                  f"Day {day_number} exceeds template max {template.total_days}"
              )
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
 class Meta:
  model=ItineraryTemplate
  fields="__all__"
  read_only_fields=("created_by","created_at","updated_at","deleted_at","code",)