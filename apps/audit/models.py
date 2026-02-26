from django.db import models
from apps.account.models import User

class AuditLog(models.Model):
 id=models.BigAutoField(primary_key=True)
 user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name="audit_logs")
 action=models.CharField(max_length=50)
 entity_type=models.CharField(max_length=50)
 entity_id=models.BigIntegerField(null=True,blank=True)
 old_values=models.JSONField(null=True,blank=True)
 new_values=models.JSONField(null=True,blank=True)
 ip_address=models.CharField(max_length=45,null=True,blank=True)
 user_agent=models.CharField(max_length=500,null=True,blank=True)
 created_at=models.DateTimeField(auto_now_add=True)

 class Meta:
  db_table="audit_logs"
  indexes=[
   models.Index(fields=["user","entity_type","action","created_at"]),
  ]

 def save(self,*args,**kwargs):
  if self.pk:
   raise Exception("AuditLog is append-only.Updates not allowed.")
  super().save(*args,**kwargs)

 def delete(self,*args,**kwargs):
  raise Exception("AuditLog cannot be deleted.")

 def __str__(self):
  return f"{self.action}-{self.entity_type}-{self.created_at}"