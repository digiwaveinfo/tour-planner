from django.contrib import admin
from .models import UserPlan,UserPlanDay,UserPlanInclExcl

@admin.register(UserPlan)
class UserPlanAdmin(admin.ModelAdmin):
 list_display=("id","plan_number","name","user","country","status","created_at")
 search_fields=("plan_number","name","client_name","client_email")
 list_filter=("status","country")
 ordering=("-created_at",)
 autocomplete_fields=("user","country","based_on_template")
 readonly_fields=("created_at","updated_at","deleted_at")

@admin.register(UserPlanDay)
class UserPlanDayAdmin(admin.ModelAdmin):
 list_display=("id","user_plan","day_number","day_tour")
 search_fields=("user_plan__plan_number","day_tour__unique_code")
 list_filter=("user_plan",)
 ordering=("user_plan","day_number")
 autocomplete_fields=("user_plan","day_tour")

@admin.register(UserPlanInclExcl)
class UserPlanInclExclAdmin(admin.ModelAdmin):
 list_display=("id","user_plan","incl_excl")
 search_fields=("user_plan__plan_number","incl_excl__unique_code","incl_excl__item_service")
 autocomplete_fields=("user_plan","incl_excl")