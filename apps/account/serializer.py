from rest_framework import serializers
from .models import User
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "name", "password"]

    def create(self, validated_data):
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

    class Meta:
        model = User
        exclude = ["password"]

class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "name", "phone", "password"]  

    def create(self, validated_data):
        request = self.context.get("request")
        role = "basic_user"
        if request and request.user.is_authenticated:
            if request.user.is_superuser or request.user.role in ["admin","superadmin"]:
                role = "agent"
            elif request.user.role == "agent":
                role = "basic_user"
        validated_data["role"] = role
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user