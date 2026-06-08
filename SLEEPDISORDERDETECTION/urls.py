from django.contrib import admin
from django.urls import path, include
from . import views

from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),

    # Static pages
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("sleep-disorders/", views.sleep_disorders, name="sleep_disorders"),

    # Apps
    # Apps
    path("accounts/", include("accounts.urls")),          # <- 1. YOUR CUSTOM APP FIRST
    path('accounts/', include('allauth.urls')),           # <- 2. ALLAUTH GOES SECOND
    path("sleep/", include("sleepdetect.urls")),          # forms
    path("predict/", include("sleep_predictor.urls")),    # ML + result
    path("patient/", include("patient.urls")),
]
