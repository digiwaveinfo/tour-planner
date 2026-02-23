import uuid
from django.db import models
from common.constant import UserRoletype

class User(models.Model):
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 name=models.CharField(max_length=150)
 email=models.EmailField(unique=True)
 phone=models.CharField(max_length=20,null=True,blank=True)
 password_hash=models.CharField(max_length=255)
 role=models.CharField(max_length=20,choices=UserRoletype.CHOICES,default="agent")
 avatar_url=models.CharField(max_length=500,null=True,blank=True)
 last_login_at=models.DateTimeField(null=True,blank=True)
 is_active=models.BooleanField(default=True)
 created_at=models.DateTimeField(auto_now_add=True)
 updated_at=models.DateTimeField(auto_now=True)
 deleted_at=models.DateTimeField(null=True,blank=True)

 class Meta:
  db_table="users"
  indexes=[
   models.Index(fields=["role","is_active","email"]),
  ]

 def __str__(self):
  return f"{self.email}-{self.role}"
 
class AgentProfile(models.Model):
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 user=models.OneToOneField(User,on_delete=models.CASCADE,related_name="agent_profile")
 agency_name=models.CharField(max_length=200)
 gst_number=models.CharField(max_length=30,null=True,blank=True)
 pan_number=models.CharField(max_length=20,null=True,blank=True)
 business_address=models.TextField(null=True,blank=True)
 city=models.CharField(max_length=100,null=True,blank=True)
 state=models.CharField(max_length=100,null=True,blank=True)
 country=models.CharField(max_length=100,default="India",null=True,blank=True)
 pincode=models.CharField(max_length=10,null=True,blank=True)
 is_verified=models.BooleanField(default=False)
 verified_at=models.DateTimeField(null=True,blank=True)
 created_at=models.DateTimeField(auto_now_add=True)
 updated_at=models.DateTimeField(auto_now=True)

 class Meta:
  db_table="agent_profiles"

 def __str__(self):
  return self.agency_name