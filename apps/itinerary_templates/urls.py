from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register("templates", ItineraryTemplateViewSet,basename="templates")
router.register("days", ItineraryTemplateDay,basename="days")
router.register("incl-excl", ItineraryTemplateInclExclViewSet,basename="incl-excl")

urlpatterns = router.urls