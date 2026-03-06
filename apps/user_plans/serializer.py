from rest_framework import serializers
from .models import UserPlan,UserPlanDay,UserPlanInclExcl

class UserPlanSerializer(serializers.ModelSerializer):
    regions = serializers.ListField(child=serializers.IntegerField(),write_only=True)
    class Meta:
        model=UserPlan
        fields = ["id","name","country","total_days","total_nights","regions"]
        read_only_fields=["user","plan_number","share_token","created_at"]

    def validate(self,data):
        regions=self.initial_data.get("regions",[])
        total_days=data.get("total_days")
        if total_days is None and self.instance:
            total_days=self.instance.total_days
        if regions and len(regions)>total_days:
            raise serializers.ValidationError("Regions cannot exceed total days")
        return data
    
    def create(self,validated_data):
        validated_data.pop("regions", None)
        return super().create(validated_data)

class UserPlanDaySerializer(serializers.ModelSerializer):
    class Meta:
        model=UserPlanDay
        fields="__all__"

class UserPlanInclExclSerializer(serializers.ModelSerializer):
    class Meta:
        model=UserPlanInclExcl
        fields="__all__"