from django.db import models

class Country(models.Model):
    id=models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3, unique=True)
    iso_code = models.CharField(max_length=3,null=True,blank=True,unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "countries"
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"
    
class Region(models.Model):
    id=models.BigAutoField(primary_key=True)
    country=models.ForeignKey(Country,on_delete=models.CASCADE,related_name="regions")
    name=models.CharField(max_length=150)
    code=models.CharField(max_length=10)
    description=models.TextField(null=True,blank=True)
    display_order=models.IntegerField(default=0)
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    deleted_at=models.DateTimeField(null=True,blank=True)

    class Meta:
        db_table="regions"

        constraints=[
            models.UniqueConstraint(fields=["country","name"],name="unique_country_name"),
            models.UniqueConstraint(fields=["country","code"],name="unique_country_code"),
        ]

        indexes=[
            models.Index(fields=["country","name"]),
        ]

    def __str__(self):
        return self.name