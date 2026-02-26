from rest_framework.viewsets import ModelViewSet
from .models import User
from rest_framework import status
from .serializer import *
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    queryset = User.objects.all().order_by("-created_at")

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return FullUserSerializer
        return UserSerializer   

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context  

    @action(detail=False, methods=["post"])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return Response({
            "message": "Login successful",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.name,
                "role": user.role,
                "is_super_admin": user.is_superuser
            },
            "tokens": {
                "access": serializer.validated_data["access"],
                "refresh": serializer.validated_data["refresh"]
            }
        })
    
    @action(detail=False, methods=["post"])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data,context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "message": "User registered successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role
            }
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def logout(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Logout successful"})   