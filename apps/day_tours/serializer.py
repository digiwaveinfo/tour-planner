from rest_framework import serializers
from .models import DayTour, DayTourAttraction

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
        read_only_fields = ("id","created_by","created_at","updated_at","deleted_at")

class DayTourAttractionSerializer(serializers.ModelSerializer):

    class Meta:
        model = DayTourAttraction
        fields = "__all__"