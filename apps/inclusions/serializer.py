from rest_framework import serializers
from apps.inclusions.models import InclusionExclusion,InclExclCategory

class InclExclCategorySerializer(serializers.ModelSerializer):
 class Meta:
  model=InclExclCategory
  fields="__all__"

class InclusionExclusionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InclusionExclusion
        fields = "__all__"
        read_only_fields = ["unique_code","created_at","updated_at","deleted_at"]