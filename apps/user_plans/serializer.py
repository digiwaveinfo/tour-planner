from rest_framework import serializers
from .models import UserPlan,UserPlanDay,UserPlanInclExcl
from apps.day_tours.serializer import DayTourSerializer

class UserPlanDaySerializer(serializers.ModelSerializer):
    day_tour_name=serializers.CharField(source="day_tour.activity_combination",read_only=True,default=None)
    region_name=serializers.CharField(source="region.name",read_only=True,default=None)
    template_name=serializers.CharField(source="template.name",read_only=True,default=None)
    includes_night=serializers.BooleanField(source="template.includes_night",read_only=True,default=False)
    day_tour_detail=DayTourSerializer(source="day_tour",read_only=True)
    class Meta:
        model=UserPlanDay
        fields="__all__"

class UserPlanInclExclSerializer(serializers.ModelSerializer):
    item_text=serializers.CharField(source="incl_excl.item_service",read_only=True)
    type=serializers.CharField(source="incl_excl.type",read_only=True)
    category_name=serializers.CharField(source="incl_excl.category.name",read_only=True)
    class Meta:
        model=UserPlanInclExcl
        fields="__all__"

class UserPlanSerializer(serializers.ModelSerializer):
    days=UserPlanDaySerializer(many=True,read_only=True)
    incl_excl=UserPlanInclExclSerializer(many=True,read_only=True)
    country_name=serializers.CharField(source="country.name",read_only=True)
    user_name=serializers.CharField(source="user.name",read_only=True)
    user_email=serializers.CharField(source="user.email",read_only=True)
    city_groups=serializers.SerializerMethodField()
    class Meta:
        model=UserPlan
        fields="__all__"
        read_only_fields=["user","plan_number","share_token","created_at"]

    def get_city_groups(self,obj):
        """Group consecutive days by region for the itinerary/summary views."""
        sorted_days=sorted(obj.days.all(),key=lambda d:d.day_number)
        groups=[]
        for day in sorted_days:
            rid=day.region_id
            rname=day.region.name if day.region else "Unknown"
            if groups and groups[-1]["region_id"]==rid:
                groups[-1]["days_count"]+=1
                groups[-1]["day_numbers"].append(day.day_number)
            else:
                groups.append({"region_id":rid,"region_name":rname,"days_count":1,"day_numbers":[day.day_number]})
        return groups