from django.urls import path
from . import views

urlpatterns = [
    path("", views.step1_basic, name="step1_basic"),
    path("bmi/", views.step2_bmi, name="step2_bmi"),
    path("activity/", views.step3_activity, name="step3_activity"),
    path("sleep_quality/", views.sleep_quality, name="sleep_quality"),
    path("stress/", views.stress_level, name="stress_level"),
    path("heart_rate/", views.heart_rate, name="heart_rate"),
    path("blood_pressure/", views.blood_pressure, name="blood_pressure"),
]
