from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Hotel
from .serializer import HotelSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import *

class HotelViewSet(ModelViewSet):
    queryset = Hotel.objects.filter(deleted_at__isnull=True)
    serializer_class = HotelSerializer
    permission_classes = [DayTourPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["country", "region", "star_rating", "is_active"]
    search_fields = ["name", "city"]
    ordering_fields = ["name", "city", "created_at"]
    ordering = ["name"]
