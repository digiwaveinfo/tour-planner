from rest_framework.routers import DefaultRouter
from .views import *

router=DefaultRouter()
router.register("inclusions-categories",InclExclCategoryViewSet,basename="inclusions-categories")
router.register("inclusions-exclusions",InclusionExclusionViewSet,basename="inclusions-exclusions")

urlpatterns=router.urls