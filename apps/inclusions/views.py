from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .models import InclExclCategory,InclusionExclusion
from .serializer import InclExclCategorySerializer,InclusionExclusionSerializer

class InclExclCategoryViewSet(ModelViewSet):
    queryset = InclExclCategory.objects.filter(is_active=True).order_by("display_order")
    serializer_class = InclExclCategorySerializer

class InclusionExclusionViewSet(ModelViewSet):
    serializer_class = InclusionExclusionSerializer

    def get_queryset(self):
        qs = InclusionExclusion.objects.filter(is_active=True)
        country = self.request.query_params.get("country")
        type_val = self.request.query_params.get("type")
        category = self.request.query_params.get("category")

        if country:
            qs = qs.filter(country_id=country)
        if type_val:
            qs = qs.filter(type=type_val)
        if category:
            qs = qs.filter(category_id=category)

        return qs.order_by("display_order")
