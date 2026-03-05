from rest_framework import serializers
from .models import DayTour, DayTourAttraction
from common.constant import TravelType, ValidityMode,CurrencyType

class DayTourAttractionListSerializer(serializers.ModelSerializer):
    attraction_name = serializers.CharField(source="attraction.name", read_only=True)

    class Meta:
        model = DayTourAttraction
        fields = ("id","attraction","attraction_name","visit_order",)

class DayTourSerializer(serializers.ModelSerializer):
    attractions = DayTourAttractionListSerializer(source="tour_attractions",many=True,read_only=True)

    class Meta:
        model = DayTour
        fields = "__all__"
        read_only_fields = ("id","created_by","created_at","updated_at","deleted_at","unique_code")

    def validate_travel_type(self, value):
        if value and value not in dict(TravelType.CHOICES):
            raise serializers.ValidationError("Invalid travel type")
        return value
    
    def validate(self, data):
        validity_mode = data.get("validity_mode")
        valid_from = data.get("valid_from")
        valid_to = data.get("valid_to")
        if validity_mode:
            if validity_mode not in dict(ValidityMode.CHOICES):
                raise serializers.ValidationError("Invalid validity mode")
            if validity_mode == ValidityMode.OPEN:
                return data
            if not valid_from:
                raise serializers.ValidationError("valid_from required")
            if validity_mode == ValidityMode.DATE_RANGE and not valid_to:
                raise serializers.ValidationError("valid_to required for date range")
            if valid_from and valid_to and valid_from > valid_to:
                raise serializers.ValidationError("valid_from cannot be greater than valid_to")
        return data 
    
    def validate_currency(self, value):
        if value not in dict(CurrencyType.CHOICES):
            raise serializers.ValidationError("Invalid currency")
        return value    

class DayTourAttractionSerializer(serializers.ModelSerializer):

    class Meta:
        model = DayTourAttraction
        fields = "__all__"