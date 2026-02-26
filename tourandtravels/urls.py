"""
URL configuration for tourandtravels project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/account/', include('apps.account.urls')),
    path('api/v1/geography/', include('apps.geography.urls')),
    path('api/v1/attractions/', include('apps.attractions.urls')),
    path('api/v1/day-tours/', include('apps.day_tours.urls')),
    path('api/v1/inclusions/', include('apps.inclusions.urls')),
    path('api/v1/itinerary-templates/', include('apps.itinerary_templates.urls')),
    path('api/v1/user-plans/', include('apps.user_plans.urls')),
    path('api/v1/audit/', include('apps.audit.urls')),
    path('api/v1/common/', include('common.urls')),
]
