from django.db import models
from apps.geography.models import Region
from apps.account.models import User
from apps.attractions.models import Attraction

class DayTour(models.Model):
 id=models.BigAutoField(primary_key=True)
 region=models.ForeignKey(Region,on_delete=models.CASCADE,related_name="day_tours")
 unique_code=models.CharField(max_length=20,unique=True)
 activity_combination=models.CharField(max_length=500)
 est_time_distance=models.CharField(max_length=200,null=True,blank=True)
 overnight_location=models.CharField(max_length=150,null=True,blank=True)
 source_file=models.CharField(max_length=200,null=True,blank=True)
 itinerary_text=models.TextField()
 display_order=models.IntegerField(default=0)
 created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name="created_day_tours")
 is_active=models.BooleanField(default=True)
 created_at=models.DateTimeField(auto_now_add=True)
 updated_at=models.DateTimeField(auto_now=True)
 deleted_at=models.DateTimeField(null=True,blank=True)

 class Meta:
  db_table="day_tours"
  indexes=[
   models.Index(fields=["region","overnight_location","is_active","created_by"]),
  ]

 def __str__(self):
  return f"{self.unique_code}-{self.region}"
 
class DayTourAttraction(models.Model):
 id=models.BigAutoField(primary_key=True)
 day_tour=models.ForeignKey(DayTour,on_delete=models.CASCADE,related_name="tour_attractions")
 attraction=models.ForeignKey(Attraction,on_delete=models.CASCADE,related_name="attraction_tours")
 visit_order=models.IntegerField(default=1)

 class Meta:
  db_table="day_tour_attractions"
  constraints=[
   models.UniqueConstraint(fields=["day_tour","attraction"],name="unique_daytour_attraction")
  ]
  indexes=[
   models.Index(fields=["day_tour"]),
   models.Index(fields=["attraction"]),
  ]

 def __str__(self):
  return f"{self.day_tour}-{self.attraction}-{self.visit_order}"