import django_filters
from .models import Attraction

class AttractionFilter(django_filters.FilterSet):
    region = django_filters.NumberFilter(field_name="region_id")
    is_active = django_filters.BooleanFilter()
    name = django_filters.CharFilter(field_name="name",lookup_expr="icontains")

    class Meta:
        model = Attraction
        fields = ["region", "is_active", "name"]