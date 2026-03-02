from rest_framework import serializers
from apps.hotel.models import Hotel,HotelImage

class HotelImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelImage
        fields = ["id", "image", "uploaded_at"]

class HotelSerializer(serializers.ModelSerializer):
 images = HotelImageSerializer(many=True, read_only=True)
 class Meta:
  model=Hotel
  fields="__all__"
  read_only_fields=("created_at","updated_at","deleted_at")