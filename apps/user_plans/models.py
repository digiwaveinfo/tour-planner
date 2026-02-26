from django.db import models
from apps.account.models import User
from apps.geography.models import Country
from apps.itinerary_templates.models import ItineraryTemplate
from apps.day_tours.models import DayTour
from apps.inclusions.models import InclusionExclusion
from common.constant import PLAN_STATUS

class UserPlan(models.Model):
 id=models.BigAutoField(primary_key=True)
 plan_number=models.CharField(max_length=20,unique=True)
 user=models.ForeignKey(User,on_delete=models.CASCADE,related_name="plans")
 country=models.ForeignKey(Country,on_delete=models.CASCADE,related_name="plans")
 based_on_template=models.ForeignKey(ItineraryTemplate,on_delete=models.SET_NULL,null=True,blank=True,related_name="derived_plans")
 client_name=models.CharField(max_length=200,null=True,blank=True)
 client_email=models.EmailField(null=True,blank=True)
 client_phone=models.CharField(max_length=20,null=True,blank=True)
 name=models.CharField(max_length=200)
 total_nights=models.IntegerField()
 total_days=models.IntegerField()
 start_date=models.DateField(null=True,blank=True)
 status=models.CharField(max_length=20,choices=PLAN_STATUS.CHOICES,default="draft")
 share_token=models.CharField(max_length=100,unique=True,null=True,blank=True)
 pdf_url=models.CharField(max_length=500,null=True,blank=True)
 notes=models.TextField(null=True,blank=True)
 created_at=models.DateTimeField(auto_now_add=True)
 updated_at=models.DateTimeField(auto_now=True)
 deleted_at=models.DateTimeField(null=True,blank=True)

 class Meta:
  db_table="user_plans"
  indexes=[
   models.Index(fields=["user","country","status","created_at"]),
  ]

 def __str__(self):
  return f"{self.plan_number}-{self.name}"

class UserPlanDay(models.Model):
 id=models.BigAutoField(primary_key=True)
 user_plan=models.ForeignKey(UserPlan,on_delete=models.CASCADE,related_name="days")
 day_number=models.IntegerField()
 day_tour=models.ForeignKey(DayTour,on_delete=models.PROTECT,related_name="plan_days")
 custom_itinerary_text=models.TextField(null=True,blank=True)
 notes=models.TextField(null=True,blank=True)
 created_at=models.DateTimeField(auto_now_add=True)
 updated_at=models.DateTimeField(auto_now=True)

 class Meta:
  db_table="user_plan_days"
  constraints=[
   models.UniqueConstraint(fields=["user_plan","day_number"],name="unique_plan_day")
  ]
  indexes=[
   models.Index(fields=["user_plan","day_tour"]),
  ]

 def __str__(self):
  return f"{self.user_plan}-{self.day_number}"

class UserPlanInclExcl(models.Model):
 id=models.BigAutoField(primary_key=True)
 user_plan=models.ForeignKey(UserPlan,on_delete=models.CASCADE,related_name="incl_excl")
 incl_excl=models.ForeignKey(InclusionExclusion,on_delete=models.CASCADE,related_name="plan_links")

 class Meta:
  db_table="user_plan_incl_excl"
  constraints=[
   models.UniqueConstraint(fields=["user_plan","incl_excl"],name="unique_plan_incl")
  ]
  indexes=[
   models.Index(fields=["user_plan","incl_excl"]),
  ]

 def __str__(self):
  return f"{self.user_plan}-{self.incl_excl}"