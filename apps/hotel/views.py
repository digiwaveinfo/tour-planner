from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Hotel,HotelImage
from .serializer import HotelSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import *
from rest_framework.parsers import MultiPartParser, FormParser

class HotelViewSet(ModelViewSet):
    queryset = Hotel.objects.filter(deleted_at__isnull=True)
    serializer_class = HotelSerializer
    permission_classes = [DayTourPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["country", "region", "star_rating", "is_active"]
    search_fields = ["name", "city"]
    ordering_fields = ["name", "city", "created_at"]
    ordering = ["name"]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        images = request.FILES.getlist("images")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        hotel = serializer.save()

        for img in images:
            HotelImage.objects.create(
                hotel=hotel,
                image=img
            )

        return Response(self.get_serializer(hotel).data)
