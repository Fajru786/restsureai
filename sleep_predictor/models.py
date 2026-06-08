# sleep_predictor/models.py
from django.db import models
from django.contrib.auth.models import User

class SleepPredictionRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_recorded = models.DateTimeField(auto_now_add=True)
    prediction = models.CharField(max_length=100)
    confidence = models.FloatField(null=True, blank=True)
    sleep_score = models.IntegerField(null=True, blank=True)
    risk_factors = models.JSONField(default=list) 
    
    # NEW FIELD: Stores the text explanation generated from SHAP
    shap_explanation = models.TextField(null=True, blank=True)

    
    # --- NEW FIELDS FOR THE DASHBOARD ---
    bmi_category = models.IntegerField(null=True, blank=True)
    physical_activity = models.FloatField(null=True, blank=True)
    sleep_quality = models.FloatField(null=True, blank=True)
    stress_level = models.FloatField(null=True, blank=True)
    heart_rate = models.IntegerField(null=True, blank=True)
    bp_systolic = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.prediction}"