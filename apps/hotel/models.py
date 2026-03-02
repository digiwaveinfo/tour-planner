from django.db import models
from apps.geography.models import Country,Region

class Hotel(models.Model):
 id = models.BigAutoField(primary_key=True)
 name=models.CharField(max_length=255)
 country=models.ForeignKey(Country,on_delete=models.CASCADE,related_name="hotels")
 region=models.ForeignKey(Region,on_delete=models.CASCADE,related_name="hotels")
 city=models.CharField(max_length=150,null=True,blank=True)
 address=models.TextField(null=True,blank=True)
 star_rating=models.IntegerField(default=3)
 hotel_type=models.CharField(max_length=100,null=True,blank=True)
 description=models.TextField(null=True,blank=True)
 contact_phone=models.CharField(max_length=20,null=True,blank=True)
 contact_email=models.EmailField(null=True,blank=True)
 website=models.CharField(max_length=500,null=True,blank=True)
 check_in_time=models.CharField(max_length=50,null=True,blank=True)
 check_out_time=models.CharField(max_length=50,null=True,blank=True)
 latitude=models.DecimalField(max_digits=10,decimal_places=7,null=True,blank=True)
 longitude=models.DecimalField(max_digits=10,decimal_places=7,null=True,blank=True)
 amenities=models.JSONField(null=True,blank=True)
 price_notes=models.CharField(max_length=255,null=True,blank=True)
 display_order=models.IntegerField(default=0)
 is_active=models.BooleanField(default=True)
 created_at=models.DateTimeField(auto_now_add=True)
 updated_at=models.DateTimeField(auto_now=True)
 deleted_at=models.DateTimeField(null=True,blank=True)

 class Meta:
  db_table="hotels"
  indexes=[
   models.Index(fields=["country","region","is_active"]),
   models.Index(fields=["name"]),
  ]

 def __str__(self):
  return self.name
 
class HotelImage(models.Model):
    id = models.BigAutoField(primary_key=True)
    hotel = models.ForeignKey(Hotel,on_delete=models.CASCADE,related_name="images")
    image = models.ImageField(upload_to="hotel_images/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hotel_images"
        indexes = [
            models.Index(fields=["hotel"]),
        ]

    def __str__(self):
        return f"{self.hotel.name} - {self.id}"