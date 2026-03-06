from django.db import models
from apps.geography.models import Country
from apps.account.models import User
from apps.day_tours.models import DayTour
from apps.inclusions.models import InclusionExclusion
from django.db.models import Q
from django.utils import timezone

class ItineraryTemplate(models.Model):
 id=models.BigAutoField(primary_key=True)
 country=models.ForeignKey(Country,on_delete=models.CASCADE,related_name="templates")
 name=models.CharField(max_length=200)
 code=models.CharField(max_length=30,unique=True,null=True,blank=True)
 total_nights=models.IntegerField(default=1,editable=False,null=True,blank=True)
 total_days=models.IntegerField(default=1,editable=False,null=True,blank=True)
 description=models.TextField(null=True,blank=True)
 is_default = models.BooleanField(default=False)
 is_active=models.BooleanField(default=True)
 created_by=models.ForeignKey(User,on_delete=models.CASCADE,related_name="created_templates")
 created_at=models.DateTimeField(auto_now_add=True)
 updated_at=models.DateTimeField(auto_now=True)
 deleted_at=models.DateTimeField(null=True,blank=True)

 class Meta:
  db_table="itinerary_templates"
  constraints = [
    models.UniqueConstraint(
        fields=["country","total_days"],
        condition=Q(is_default=True),
        name="unique_default_template_per_country_days"
    )
]
  indexes=[
   models.Index(fields=["country","is_active","created_by"]),
  ]

 def __str__(self):
  return self.name
 
 def generate_code(self):
    today = timezone.now().strftime("%Y%m%d")
    prefix = "ITN"
    last = ItineraryTemplate.objects.filter(
        code__startswith=f"{prefix}-{today}"
    ).order_by("-code").first()
    if last:
        last_number = int(last.code.split("-")[-1])
        new_number = last_number + 1
    else:
        new_number = 1
    return f"{prefix}-{today}-{str(new_number).zfill(4)}"
 
 def save(self, *args, **kwargs):
    self.total_days = 1
    self.total_nights = 1
    self.is_default = True
    if not self.code:
        self.code = self.generate_code()
    super().save(*args, **kwargs)
 
class ItineraryTemplateDay(models.Model):
 id=models.BigAutoField(primary_key=True)
 template=models.ForeignKey(ItineraryTemplate,on_delete=models.CASCADE,related_name="days")
 day_number=models.IntegerField()
 day_tour=models.ForeignKey(DayTour,on_delete=models.PROTECT,related_name="template_days")
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
   models.Index(fields=["template","day_tour"]),
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