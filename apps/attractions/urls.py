from rest_framework.routers import DefaultRouter
from .views import AttractionViewSet

router = DefaultRouter()
router.register("attract", AttractionViewSet,basename="attractions")

urlpatterns = router.urls