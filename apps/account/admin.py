from django.contrib import admin
from .models import User,AgentProfile

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
 list_display=("id","email","name","role","is_active","created_at")
 search_fields=("email","name","phone")
 list_filter=("role","is_active")
 ordering=("email",)
 readonly_fields=("created_at","updated_at","deleted_at")

@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
 list_display=("id","agency_name","user","city","state","is_verified")
 search_fields=("agency_name","user__email","gst_number","pan_number")
 list_filter=("is_verified","state","city")
 autocomplete_fields=("user",)
 readonly_fields=("created_at","updated_at")