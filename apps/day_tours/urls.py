from rest_framework.routers import DefaultRouter
from .views import DayTourViewSet

router = DefaultRouter()
router.register("day", DayTourViewSet, basename="daytour")

urlpatterns = router.urls