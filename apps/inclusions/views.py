from rest_framework.viewsets import ModelViewSet
from .models import InclExclCategory,InclusionExclusion
from .serializer import InclExclCategorySerializer,InclusionExclusionSerializer
from rest_framework.decorators import action
from collections import defaultdict
from rest_framework.response import Response
from common.permissions import DayTourPermission

class InclExclCategoryViewSet(ModelViewSet):
    queryset = InclExclCategory.objects.filter(is_active=True).order_by("display_order")
    serializer_class = InclExclCategorySerializer
    permission_classes = [DayTourPermission]

class InclusionExclusionViewSet(ModelViewSet):
    serializer_class = InclusionExclusionSerializer
    permission_classes = [DayTourPermission]

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

    @action(detail=False, methods=["get"], url_path="grouped")
    def grouped(self, request):
        country = request.query_params.get("country")
        if not country: 
            return Response({"error": "country required"}, status=400)
        qs = InclusionExclusion.objects.filter(country_id=country,is_active=True).select_related("category")

        data = {
            "INCLUSION": defaultdict(list),
            "EXCLUSION": defaultdict(list)
        }

        for item in qs:
            data[item.type][item.category.name].append({
                "id": item.id,
                "service": item.item_service,
                "notes": item.details_notes
            })

        return Response(data)
