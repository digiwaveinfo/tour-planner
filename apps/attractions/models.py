from django.db import models
from apps.geography.models import Region

class Attraction(models.Model):
 id=models.BigAutoField(primary_key=True)
 region=models.ForeignKey(Region,on_delete=models.CASCADE,related_name="attractions")
 reference_no=models.CharField(max_length=20,unique=True)
 name=models.CharField(max_length=200)
 key_features_notes=models.TextField(null=True,blank=True)
 source_citations=models.TextField(null=True,blank=True)
 image_url=models.CharField(max_length=500,null=True,blank=True)
 latitude=models.DecimalField(max_digits=10,decimal_places=7,null=True,blank=True)
 longitude=models.DecimalField(max_digits=10,decimal_places=7,null=True,blank=True)
 display_order=models.IntegerField(default=0)
 is_active=models.BooleanField(default=True)
 created_at=models.DateTimeField(auto_now_add=True)
 updated_at=models.DateTimeField(auto_now=True)
 deleted_at=models.DateTimeField(null=True,blank=True)

 class Meta:
  db_table="attractions"
  indexes=[
   models.Index(fields=["region","name","is_active"]),
  ]

 def __str__(self):
  return f"{self.name}-{self.reference_no}"