from django.db import models
from apps.geography.models import Country
from common.constant import InclusionExclusionType

class InclExclCategory(models.Model):
 id=models.BigAutoField(primary_key=True)
 name=models.CharField(max_length=100,unique=True)
 display_order=models.IntegerField(default=0)
 is_active=models.BooleanField(default=True)
 created_at=models.DateTimeField(auto_now_add=True)
 updated_at=models.DateTimeField(auto_now=True)

 class Meta:
  db_table="incl_excl_categories"

 def __str__(self):
  return self.name
 
class InclusionExclusion(models.Model):
 id=models.BigAutoField(primary_key=True)
 country=models.ForeignKey(Country,on_delete=models.CASCADE,related_name="incl_excl")
 unique_code=models.CharField(max_length=20,unique=True)
 type=models.CharField(max_length=10,choices=InclusionExclusionType.CHOICES)
 category=models.ForeignKey(InclExclCategory,on_delete=models.PROTECT,related_name="items")
 item_service=models.CharField(max_length=200)
 details_notes=models.TextField(null=True,blank=True)
 source_files=models.TextField(null=True,blank=True)
 display_order=models.IntegerField(default=0)
 is_active=models.BooleanField(default=True)
 created_at=models.DateTimeField(auto_now_add=True)
 updated_at=models.DateTimeField(auto_now=True)
 deleted_at=models.DateTimeField(null=True,blank=True)

 class Meta:
  db_table="inclusions_exclusions"
  indexes=[
   models.Index(fields=["country","type","category"]),
   models.Index(fields=["country","type"]),
   models.Index(fields=["is_active"]),
  ]

 def __str__(self):
  return f"{self.unique_code}-{self.item_service}"