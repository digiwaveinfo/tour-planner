from rest_framework.routers import DefaultRouter
from .views import CountryViewSet,RegionViewSet

router = DefaultRouter()
router.register("countries", CountryViewSet, basename="countries")
router.register("regions", RegionViewSet, basename="regions")

urlpatterns = router.urls