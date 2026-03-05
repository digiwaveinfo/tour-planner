from django.db import models
from apps.geography.models import Region
from django.utils import timezone

class Attraction(models.Model):
 id=models.BigAutoField(primary_key=True)
 region=models.ForeignKey(Region,on_delete=models.CASCADE,related_name="attractions")
 reference_no=models.CharField(max_length=20,unique=True)
 name=models.CharField(max_length=200)
 key_features_notes=models.TextField(null=True,blank=True)
 source_citations=models.TextField(null=True,blank=True)
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
   models.Index(fields=["reference_no","region","name","is_active"]),
  ]

 def __str__(self):
  return f"{self.name}-{self.reference_no}"
 
 def generate_reference_no(self):
        today = timezone.now().strftime("%Y%m%d")
        last = Attraction.objects.filter(
            reference_no__startswith=f"ATT-{today}").order_by("-reference_no").first()
        if last:
            last_number = int(last.reference_no.split("-")[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        return f"ATT-{today}-{str(new_number).zfill(4)}"

 def save(self, *args, **kwargs):
        if not self.reference_no:
            self.reference_no = self.generate_reference_no()
        super().save(*args, **kwargs)
 
class AttractionImage(models.Model):
 id = models.BigAutoField(primary_key=True)
 attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE, related_name="images")
 image = models.ImageField(upload_to="attraction_images/")
 uploaded_at = models.DateTimeField(auto_now_add=True)

 class Meta:
  db_table = "attraction_images"
  indexes = [
   models.Index(fields=["attraction"]),
  ]

 def __str__(self):
  return f"{self.attraction.name} - {self.id}"