from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .models import Country,Region
from .serializer import CountrySerializer,RegionSerializer
from common.permissions import *
from rest_framework.decorators import action
from rest_framework.response import Response

class CountryViewSet(ModelViewSet):
    queryset = Country.objects.filter(deleted_at__isnull=True)
    serializer_class = CountrySerializer
    permission_classes = [IsSuperAdminOrAdminWriteElseReadOnly]

class RegionViewSet(ModelViewSet):
    serializer_class = RegionSerializer
    permission_classes = [IsSuperAdminOrAdminWriteElseReadOnly]

    def get_queryset(self):
        qs = Region.objects.select_related("country")
        country_id = self.request.query_params.get("country")
        if country_id:
            qs = qs.filter(country_id=country_id)
        return qs

    @action(detail=True, methods=["get"])
    def regions(self, request, pk=None):
        regions = Region.objects.filter(country_id=pk)
        serializer = RegionSerializer(regions, many=True)
        return Response(serializer.data)
