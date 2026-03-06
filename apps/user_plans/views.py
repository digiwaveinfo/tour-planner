from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserPlan,UserPlanDay,UserPlanInclExcl
from .serializer import UserPlanSerializer,UserPlanDaySerializer,UserPlanInclExclSerializer
from .utils import generate_plan_number,generate_share_token
from common.permissions import DayTourPermission
from apps.itinerary_templates.models import ItineraryTemplate
from apps.day_tours.models import DayTour
import math

class UserPlanViewSet(ModelViewSet):
    serializer_class=UserPlanSerializer
    permission_classes=[DayTourPermission,IsAuthenticated]

    def get_queryset(self):
        return UserPlan.objects.filter(user=self.request.user).order_by("-id")

    def create(self,request,*args,**kwargs):
        serializer=self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        regions=serializer.initial_data.get("regions",[])
        total_days=serializer.validated_data["total_days"]
        plan=serializer.save(user=request.user,plan_number=generate_plan_number(),share_token=generate_share_token())
        current_day=1
        first_city_days=math.ceil(total_days*0.5)
        remaining_days=total_days-first_city_days
        remaining_cities=max(len(regions)-1,1)
        for index,region in enumerate(regions):
            if index==0:
                days=first_city_days
            else:
                days=max(remaining_days//remaining_cities,1)
            template=ItineraryTemplate.objects.filter(
                days__day_tour__region_id=region,
                is_default=True,
                is_active=True
            ).first()
            if template and template.days.exists():
                tour=template.days.first().day_tour
            else:
                tour=DayTour.objects.filter(
                    region_id=region,
                    is_active=True
                ).first()
            for i in range(days):
                if current_day>total_days:
                    break
                if tour:
                    UserPlanDay.objects.create(
                        user_plan=plan,
                        day_number=current_day,
                        day_tour=tour
                    )
                current_day+=1
        return Response({
            "message":"Plan created successfully",
            "plan_id":plan.id
        })
    def update(self,request,*args,**kwargs):
        instance=self.get_object()
        serializer=self.get_serializer(instance,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        regions=serializer.initial_data.get("regions")
        plan=serializer.save()
        if regions:
            plan.days.all().delete()
            total_days=plan.total_days
            current_day=1
            first_city_days=math.ceil(total_days*0.5)
            remaining_days=total_days-first_city_days
            remaining_cities=max(len(regions)-1,1)
            for index,region in enumerate(regions):
                if index==0:
                    days=first_city_days
                else:
                    days=max(remaining_days//remaining_cities,1)
                tour=DayTour.objects.filter(
                    region_id=region,
                    is_active=True
                ).first()
                for i in range(days):
                    if current_day>total_days:
                        break
                    if tour:
                        UserPlanDay.objects.create(
                            user_plan=plan,
                            day_number=current_day,
                            day_tour=tour
                        )
                    current_day+=1
        return Response({
            "message":"Plan updated successfully"
        })
    
    @action(detail=True,methods=["get"])
    def summary(self,request,pk=None):
        plan=self.get_object()
        data={
            "plan":{
                "id":plan.id,
                "name":plan.name,
                "country":plan.country.name,
                "days":plan.total_days,
                "nights":plan.total_nights,
                "status":plan.status
            },"itinerary":[]}
        for d in plan.days.all().order_by("day_number"):
            data["itinerary"].append({
                "day":d.day_number,
                "tour":{
                    "id":d.day_tour.id,
                    "code":d.day_tour.unique_code,
                    "region":d.day_tour.region.name,
                    "itinerary_text":d.day_tour.itinerary_text,
                    "price":d.day_tour.price,
                    "currency":d.day_tour.currency},
                "attractions":[
                    {
                        "id":a.attraction.id,
                        "name":a.attraction.name
                    }
                    for a in d.day_tour.tour_attractions.all()]})
        return Response(data)

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
            user_plan__user=self.request.user)

class UserPlanInclExclViewSet(ModelViewSet):
    serializer_class=UserPlanInclExclSerializer
    permission_classes=[DayTourPermission,IsAuthenticated]

    def get_queryset(self):
        return UserPlanInclExcl.objects.filter(
            user_plan__user=self.request.user)