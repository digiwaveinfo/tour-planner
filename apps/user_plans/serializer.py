from rest_framework import serializers
from .models import UserPlan,UserPlanDay,UserPlanInclExcl

class UserPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model=UserPlan
        fields="__all__"
        read_only_fields=["user","plan_number","share_token","created_at"]

class UserPlanDaySerializer(serializers.ModelSerializer):
    class Meta:
        model=UserPlanDay
        fields="__all__"

class UserPlanInclExclSerializer(serializers.ModelSerializer):
    class Meta:
        model=UserPlanInclExcl
        fields="__all__"