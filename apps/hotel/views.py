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

    def update(self, request, *args, **kwargs):
        images = request.FILES.getlist("images")
        remove_images = request.data.getlist("remove_images") if hasattr(request.data, 'getlist') else request.data.get("remove_images", [])
        if isinstance(remove_images, str):
            remove_images = [remove_images]

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        hotel = serializer.save()

        if remove_images:
            HotelImage.objects.filter(
                id__in=[int(i) for i in remove_images],
                hotel=hotel
            ).delete()

        for img in images:
            HotelImage.objects.create(hotel=hotel, image=img)

        return Response(self.get_serializer(hotel).data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
