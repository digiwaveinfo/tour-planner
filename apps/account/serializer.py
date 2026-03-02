from rest_framework import serializers
from .models import User
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from common.constant import UserRoletype
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "name", "password","flag"]

    def create(self, validated_data):
        request = self.context.get("request")
        role = UserRoletype.USER
        if request and request.user.is_authenticated:
            if request.user.role == UserRoletype.SUPER_ADMIN:
                role = UserRoletype.AGENT
            elif request.user.role == UserRoletype.AGENT:
                role = UserRoletype.USER
        validated_data["role"] = role
        validated_data["created_by"] = request.user if request and request.user.is_authenticated else None
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        try:
            user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email")
        if not user.check_password(data["password"]):
            raise serializers.ValidationError("Wrong password")
        refresh = RefreshToken.for_user(user)
        return {
            "user": user,
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        } 

class FullUserSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = User
        exclude = ["password"]

    def get_created_by(self, obj):
        if obj.created_by:
            return {
                "id": obj.created_by.id,
                "name": obj.created_by.name,
                "email": obj.created_by.email,
                "role": obj.created_by.role
            }
        return None

class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "name", "phone", "password"]  

    def create(self, validated_data):
        request = self.context.get("request")
        role = UserRoletype.USER
        if request and request.user.is_authenticated:
            if request.user.role == UserRoletype.SUPER_ADMIN:
                role = UserRoletype.AGENT
            elif request.user.role == UserRoletype.AGENT:
                role = UserRoletype.USER
        validated_data["role"] = role
        validated_data["created_by"] = request.user if request and request.user.is_authenticated else None
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs["refresh"]
        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except Exception:
            raise serializers.ValidationError("Invalid refresh token")