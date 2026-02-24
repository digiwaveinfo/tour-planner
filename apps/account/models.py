from django.db import models
from common.constant import UserRoletype
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser,PermissionsMixin):
 id=models.BigAutoField(primary_key=True)
 name=models.CharField(max_length=150)
 email=models.EmailField(unique=True)
 phone=models.CharField(max_length=20,null=True,blank=True)
 role=models.CharField(max_length=20,choices=UserRoletype.CHOICES,default=UserRoletype.BASIC_USER)
 avatar_url=models.CharField(max_length=500,null=True,blank=True)
 last_login_at=models.DateTimeField(null=True,blank=True)
 is_active=models.BooleanField(default=True)
 is_staff=models.BooleanField(default=False)
 created_at=models.DateTimeField(auto_now_add=True)
 updated_at=models.DateTimeField(auto_now=True)
 deleted_at=models.DateTimeField(null=True,blank=True)

 objects = UserManager()

 USERNAME_FIELD = "email"
 REQUIRED_FIELDS = []

 class Meta:
  db_table="users"
  indexes=[
   models.Index(fields=["role","is_active","email"]),
  ]

 def __str__(self):
  return self.email
 
 def has_perm(self, perm, obj=None):
  return True

 def has_module_perms(self, app_label):
  return True

class AgentProfile(models.Model):
 id=models.BigAutoField(primary_key=True)
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