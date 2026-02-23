from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
 list_display=("id","user","action","entity_type","entity_id","created_at")
 search_fields=("entity_type","action","user__email")
 list_filter=("action","entity_type","created_at")
 ordering=("-created_at",)
 autocomplete_fields=("user",)
 readonly_fields=("user","action","entity_type","entity_id","old_values","new_values","ip_address","user_agent","created_at")

 def has_add_permission(self,request):
  return False