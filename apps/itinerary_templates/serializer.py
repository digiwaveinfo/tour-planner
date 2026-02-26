from rest_framework import serializers
from apps.itinerary_templates.models import *

class ItineraryTemplateSerializer(serializers.ModelSerializer):
 class Meta:
  model=ItineraryTemplate
  fields="__all__"
  read_only_fields=("created_by","created_at","updated_at","deleted_at")

class ItineraryTemplateDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItineraryTemplateDay
        fields = "__all__"

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
    class Meta:
        model = ItineraryTemplateInclExcl
        fields = "__all__"