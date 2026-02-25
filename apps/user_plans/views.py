from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserPlan,UserPlanDay,UserPlanInclExcl
from .serializer import UserPlanSerializer,UserPlanDaySerializer,UserPlanInclExclSerializer
from .utils import generate_plan_number,generate_share_token
from common.permissions import DayTourPermission

class UserPlanViewSet(ModelViewSet):
    serializer_class=UserPlanSerializer
    permission_classes=[DayTourPermission,IsAuthenticated]

    def get_queryset(self):
        return UserPlan.objects.filter(user=self.request.user).order_by("-id")

    def perform_create(self,serializer):
        serializer.save(
            user=self.request.user,
            plan_number=generate_plan_number(),
            share_token=generate_share_token()
        )

    @action(detail=True,methods=["post"])
    def clone(self,request,pk=None):
        old=self.get_object()

        new_plan=UserPlan.objects.create(
            user=request.user,
            country=old.country,
            name=old.name+" Copy",
            total_days=old.total_days,
            total_nights=old.total_nights,
            plan_number=generate_plan_number(),
            share_token=generate_share_token()
        )

        for d in old.days.all():
            UserPlanDay.objects.create(
                user_plan=new_plan,
                day_number=d.day_number,
                day_tour=d.day_tour,
                custom_itinerary_text=d.custom_itinerary_text,
                notes=d.notes
            )

        for i in old.incl_excl.all():
            UserPlanInclExcl.objects.create(
                user_plan=new_plan,
                incl_excl=i.incl_excl
            )

        return Response({
            "message":"Plan cloned successfully",
            "new_plan_id":new_plan.id
        })
    
class UserPlanDayViewSet(ModelViewSet):
    serializer_class=UserPlanDaySerializer
    permission_classes=[DayTourPermission,IsAuthenticated]

    def get_queryset(self):
        return UserPlanDay.objects.filter(
            user_plan__user=self.request.user
        )
    
class UserPlanInclExclViewSet(ModelViewSet):
    serializer_class=UserPlanInclExclSerializer
    permission_classes=[DayTourPermission,IsAuthenticated]

    def get_queryset(self):
        return UserPlanInclExcl.objects.filter(
            user_plan__user=self.request.user
        )