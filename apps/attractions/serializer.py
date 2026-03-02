from rest_framework import serializers
from apps.attractions.models import Attraction,AttractionImage

class AttractionImageSerializer(serializers.ModelSerializer):
 class Meta:
  model = AttractionImage
  fields = "__all__"
  
class AttractionSerializer(serializers.ModelSerializer):
 images = AttractionImageSerializer(many=True, read_only=True)
 class Meta:
  model=Attraction
  fields="__all__"
