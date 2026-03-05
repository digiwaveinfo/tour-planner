from rest_framework import serializers
from .models import UserPlan,UserPlanDay,UserPlanInclExcl

class UserPlanDaySerializer(serializers.ModelSerializer):
    day_tour_name=serializers.CharField(source="day_tour.activity_combination",read_only=True)
    region_name=serializers.CharField(source="day_tour.region.name",read_only=True)
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
    user_name=serializers.CharField(source="user.full_name",read_only=True)
    user_email=serializers.CharField(source="user.email",read_only=True)
    class Meta:
        model=UserPlan
        fields="__all__"
        read_only_fields=["user","plan_number","share_token","created_at"]