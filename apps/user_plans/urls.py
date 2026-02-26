from rest_framework.routers import DefaultRouter
from .views import *

router=DefaultRouter()
router.register("plans",UserPlanViewSet,basename="plans")
router.register("plan-days",UserPlanDayViewSet,basename="plan-days")
router.register("plan-incl",UserPlanInclExclViewSet,basename="plan-incl")

urlpatterns=router.urls