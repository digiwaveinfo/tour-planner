from rest_framework.routers import DefaultRouter
from .views import *

router=DefaultRouter()
router.register("categories",InclExclCategoryViewSet,basename="categories")
router.register("exclusions",InclusionExclusionViewSet,basename="exclusions")

urlpatterns=router.urls