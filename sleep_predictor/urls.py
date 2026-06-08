from django.urls import path

from . import views

urlpatterns = [
    path("result/", views.predict_result, name="predict_result"),
    path("analytics/", views.analytics_dashboard, name="analytics_dashboard"),
    path("chatbot/", views.ai_chatbot, name="ai_chatbot"),
    path('contact/', views.contact_view, name='contact'),
    
]
