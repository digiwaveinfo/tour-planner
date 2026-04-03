from django.db import models
from apps.geography.models import Country, Region
from apps.account.models import User
from apps.day_tours.models import DayTour
from apps.inclusions.models import InclusionExclusion
from django.db.models import Q

class ItineraryTemplate(models.Model):
 TRAVEL_TYPE_CHOICES = [
     ('COUPLE', 'Couple'),
     ('GROUP', 'Group'),
     ('SOLO', 'Solo'),
 ]

 id=models.BigAutoField(primary_key=True)
 country=models.ForeignKey(Country,on_delete=models.CASCADE,related_name="templates")
 region=models.ForeignKey(Region,on_delete=models.SET_NULL,null=True,blank=True,related_name="templates",help_text="City/region this single-day template belongs to.")
 name=models.CharField(max_length=200)
 code=models.CharField(max_length=30,unique=True,null=True,blank=True)
 # For single-day templates total_days is always 1; total_nights is 0 or 1 (set by save())
 total_nights=models.IntegerField(default=0)
 total_days=models.IntegerField(default=1)
 # Admin sets this: True = Day + Night stay; False = Day tour only
 includes_night=models.BooleanField(default=False,help_text="If True, this template includes an overnight stay (1D/1N). If False, it is a day tour only (1D/0N).")
 travel_type=models.CharField(max_length=10,choices=TRAVEL_TYPE_CHOICES,null=True,blank=True)
 description=models.TextField(null=True,blank=True)
 is_default = models.BooleanField(default=False)
 is_active=models.BooleanField(default=True)
 created_by=models.ForeignKey(User,on_delete=models.CASCADE,related_name="created_templates")
 created_at=models.DateTimeField(auto_now_add=True)
 updated_at=models.DateTimeField(auto_now=True)
 deleted_at=models.DateTimeField(null=True,blank=True)

 class Meta:
  db_table="itinerary_templates"
  constraints=[
   models.UniqueConstraint(
    fields=["region"],
    condition=Q(is_default=True,region__isnull=False),
    name="unique_default_template_per_region"
   ),
  ]
  indexes=[
   models.Index(fields=["country","is_active","created_by"]),
   models.Index(fields=["region","is_default","is_active"]),
  ]

 def save(self,*args,**kwargs):
  """Always single-day: enforce total_days=1 and derive total_nights from includes_night."""
  self.total_days=1
  self.total_nights=1 if self.includes_night else 0
  super().save(*args,**kwargs)

 def __str__(self):
  return self.name
 
class ItineraryTemplateDay(models.Model):
 id=models.BigAutoField(primary_key=True)
 template=models.ForeignKey(ItineraryTemplate,on_delete=models.CASCADE,related_name="days")
 day_number=models.IntegerField()
 morning_tour=models.ForeignKey(DayTour,on_delete=models.SET_NULL,null=True,blank=True,related_name="template_morning_days")
 noon_tour=models.ForeignKey(DayTour,on_delete=models.SET_NULL,null=True,blank=True,related_name="template_noon_days")
 night_tour=models.ForeignKey(DayTour,on_delete=models.SET_NULL,null=True,blank=True,related_name="template_night_days")
 custom_notes=models.TextField(null=True,blank=True)
 is_arrival_day=models.BooleanField(default=False)
 is_departure_day=models.BooleanField(default=False)
 display_order=models.IntegerField(default=0)

 class Meta:
  db_table="itinerary_template_days"
  constraints=[
   models.UniqueConstraint(fields=["template","day_number"],name="unique_template_day")
  ]
  indexes=[
   models.Index(fields=["template","morning_tour","noon_tour","night_tour"]),
  ]

 def __str__(self):
  return f"{self.template}-{self.day_number}"
 
class ItineraryTemplateInclExcl(models.Model):
 id=models.BigAutoField(primary_key=True)
 template=models.ForeignKey(ItineraryTemplate,on_delete=models.CASCADE,related_name="incl_excl")
 incl_excl=models.ForeignKey(InclusionExclusion,on_delete=models.CASCADE,related_name="template_links")

 class Meta:
  db_table="itinerary_template_incl_excl"
  constraints=[
   models.UniqueConstraint(fields=["template","incl_excl"],name="unique_template_incl")
  ]
  indexes=[
   models.Index(fields=["template","incl_excl"]),
  ]

 def __str__(self):
  return f"{self.template}-{self.incl_excl}"