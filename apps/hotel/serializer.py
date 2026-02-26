from rest_framework import serializers
from apps.hotel.models import Hotel

class HotelSerializer(serializers.ModelSerializer):
 class Meta:
  model=Hotel
  fields="__all__"
  read_only_fields=("created_at","updated_at","deleted_at")