from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import SleepPredictionRecord

import os
import pickle
import uuid
import numpy as np
import pandas as pd
import shap
import matplotlib
matplotlib.use("Agg")   # IMPORTANT for Django servers
import matplotlib.pyplot as plt
import io
import base64
import traceback

# Import Groq instead of OpenAI
from groq import Groq

# ================================
# LOAD ML FILES
# ================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model = pickle.load(open(
    os.path.join(BASE_DIR, "ml", "soft_voting.pkl"), "rb"
))
scaler = pickle.load(open(
    os.path.join(BASE_DIR, "ml", "scaler.pkl"), "rb"
))
label_encoder = pickle.load(open(
    os.path.join(BASE_DIR, "ml", "label_encoder.pkl"), "rb"
))
occupation_encoder = pickle.load(open(
    os.path.join(BASE_DIR, "ml", "occupation_encoder.pkl"), "rb"
))

# ================================
# INITIALIZE GROQ CLIENT
# ================================
try:
    client = Groq(api_key=settings.GROQ_API_KEY)
except Exception as e:
    print(f"Groq initialization warning: {e}")
    client = None

# ================================
# FINAL ML PREDICTION
# ================================
@login_required(login_url='login')
def predict_result(request):
    # REQUIRED FIELDS CHECK
    # ==============================
    required = [
        "gender", "age", "occupation", "sleep_duration", "sleep_quality",
        "physical_activity", "stress_level", "bmi_category",
        "bp_systolic", "heart_rate", "daily_steps"
    ]

    missing = [k for k in required if request.session.get(k) is None]
    if missing:
        return render(
            request,
            "sleepdetect/debug_missing.html",
            {"missing": missing}
        )
    
    # FEATURE PREPARATION
    # ==============================
    gender_map = {"Male": 0, "Female": 1, "Other": 2}
    activity_rating = float(request.session["physical_activity"])
    activity_minutes = int((activity_rating / 10) * 180)

    features = [[
        gender_map[request.session["gender"]],
        request.session["age"],
        occupation_encoder.transform([request.session["occupation"].strip()])[0],
        request.session["sleep_duration"],
        request.session["sleep_quality"],
        activity_minutes,
        request.session["stress_level"],
        request.session["bmi_category"],
        request.session["bp_systolic"],
        request.session["heart_rate"],
        request.session["daily_steps"],
    ]]

    # FIXED: Column names exactly match what the StandardScaler saw during fit()
    feature_names = [
        "Gender", 
        "Age", 
        "Occupation", 
        "Sleep Duration", 
        "Quality of Sleep",
        "Physical Activity Level", 
        "Stress Level", 
        "BMI Category",
        "Blood Pressure", 
        "Heart Rate", 
        "Daily Steps"
    ]
    
    # Convert to DataFrame before scaling
    unscaled_df = pd.DataFrame(features, columns=feature_names)
    scaled = scaler.transform(unscaled_df)
    
    # Create user_df for SHAP using the same column names
    user_df = pd.DataFrame(scaled, columns=feature_names)

    # ML PREDICTION
    # ==============================
    pred = model.predict(scaled)[0]
    prediction = label_encoder.inverse_transform([pred])[0]

    try:
        probs = model.predict_proba(scaled)[0]
        confidence = round(max(probs) * 100, 2)
    except:
        confidence = 0

    # GENERATE SHAP EXPLANATION
    # ==============================
    shap_text = "The AI used a balanced combination of your inputs to make this prediction."
    image_base64 = None
    try:
        proxy_model = model
        if hasattr(model, 'estimators_'):
            for est in model.estimators_:
                if type(est).__name__ in ['RandomForestClassifier', 'DecisionTreeClassifier', 'XGBClassifier', 'LGBMClassifier', 'GradientBoostingClassifier']:
                    proxy_model = est
                    break

        explainer = shap.TreeExplainer(proxy_model) 
        shap_values = explainer(user_df)

        plt.figure(figsize=(8, 5))
        predicted_class_index = int(pred)
        explanation_for_prediction = shap_values[0, :, predicted_class_index]
        
        shap.waterfall_plot(explanation_for_prediction, show=False) 
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
        plt.close()
        
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        # Generate Patient-Friendly Text from SHAP Values
        feature_impacts = list(zip(feature_names, explanation_for_prediction.values))
        feature_impacts.sort(key=lambda x: x[1], reverse=True) 
        top_factors = [f[0] for f in feature_impacts if f[1] > 0][:2]
        
        if len(top_factors) >= 2:
            shap_text = f"Your {top_factors[0]} and {top_factors[1]} were the main factors driving this prediction."
        elif len(top_factors) == 1:
            shap_text = f"Your {top_factors[0]} was the primary factor driving this prediction."

    except Exception as e:
        image_base64 = f"ERROR: {str(e)}"
        shap_text = "Explanation temporarily unavailable."

    # Calculate sleep score from sleep quality
    sleep_score = int((request.session["sleep_quality"] / 10) * 100)

    # GET AI ADVICE FROM GROQ
    # ==============================
    groq_response = "Unable to generate AI advice at this time."
    if client:
        try:
            prompt = f"""
            Based on the following sleep disorder prediction data, provide brief, actionable health advice:
            - Prediction: {prediction}
            - Confidence: {confidence}%
            - Sleep Duration: {request.session.get("sleep_duration")} hours
            - Sleep Quality: {request.session.get("sleep_quality")}/10
            - Stress Level: {request.session.get("stress_level")}/10
            - Physical Activity: {request.session.get("physical_activity")}/10
            
            Please provide 2-3 sentences of practical, evidence-based advice.
            """
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            groq_response = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq API error: {e}")
            groq_response = "AI advice unavailable. Please consult healthcare professionals."

    # DYNAMIC RISK EXPLANATION (SHAP-BASED)
    # ==============================
    risk_factors = []
    
    # Create a dictionary of feature impacts for easy lookup
    shap_impacts = dict(zip(feature_names, explanation_for_prediction.values))

    def get_impact_pct(feature_name):
        # Convert raw SHAP value to a readable percentage-style weight
        val = shap_impacts.get(feature_name, 0)
        return f"{'+' if val > 0 else ''}{round(val * 100, 1)}%"

    # 1. Sleep Duration
    dur = request.session["sleep_duration"]
    impact = get_impact_pct("Sleep Duration")
    if dur < 6:
        risk_factors.append(f"Sleep duration: {dur} hrs ({impact})")
    else:
        risk_factors.append(f"Sleep duration: Adequate ({dur} hrs) ({impact})")

    # 2. Stress Level
    stress = request.session["stress_level"]
    impact = get_impact_pct("Stress Level")
    if stress > 7:
        risk_factors.append(f"Stress level: Very high ({impact})")
    else:
        risk_factors.append(f"Stress level: Normal/Moderate ({impact})")

    # 3. Physical Activity
    activity = request.session["physical_activity"]
    impact = get_impact_pct("Physical Activity Level")
    if activity < 5:
        risk_factors.append(f"Physical activity: Low ({impact})")
    else:
        risk_factors.append(f"Physical activity: Good ({impact})")

    # 4. Blood Pressure
    bp = request.session["bp_systolic"]
    impact = get_impact_pct("Blood Pressure")
    if bp > 135:
        risk_factors.append(f"Blood pressure: Elevated ({bp} mmHg) ({impact})")
    else:
        risk_factors.append(f"Blood pressure: Normal ({bp} mmHg) ({impact})")

    # 5. BMI Category
    impact = get_impact_pct("BMI Category")
    if request.session["bmi_category"] in [2, 3]:   
        risk_factors.append(f"BMI category: Above healthy range ({impact})")
    else:
        risk_factors.append(f"BMI category: Healthy range ({impact})")

    # SAVE DATA PERMANENTLY TO DB
    # ==============================
    SleepPredictionRecord.objects.create(
        user=request.user,
        prediction=prediction,
        confidence=confidence,
        sleep_score=sleep_score,
        risk_factors=risk_factors,
        shap_explanation=shap_text,
        bmi_category=request.session.get("bmi_category"),
        physical_activity=request.session.get("physical_activity"),
        sleep_quality=request.session.get("sleep_quality"),
        stress_level=request.session.get("stress_level"),
        heart_rate=request.session.get("heart_rate"),
        bp_systolic=request.session.get("bp_systolic")
    )

    request.session["prediction"] = prediction
    request.session["risk_factors"] = risk_factors
    request.session["sleep_score"] = sleep_score
    request.session["confidence"] = confidence
    
    if "chat_history" in request.session:
        del request.session["chat_history"]

    return render(
        request,
        "sleepdetect/predict_result.html",
        {
            "prediction": prediction,
            "risk_factors": risk_factors,
            "sleep_score": sleep_score,
            "confidence": confidence,
            "groq_advice": groq_response,
            "shap_graph": image_base64,
            "shap_text": shap_text,
        }
    )

# ================================
# ANALYTICS DASHBOARD
# ================================
@login_required(login_url='login')
def analytics_dashboard(request):
    latest_record = SleepPredictionRecord.objects.filter(user=request.user).order_by('-date_recorded').first()
    context = {
        "prediction": "No prediction available", "risk_factors": [], "sleep_score": 0, "date_recorded": None,
        "bmi": None, "physical_activity": None, "sleep_quality": None, "stress_level": None,
        "heart_rate": None, "bp_systolic": None,
    }
    if latest_record:
        context["prediction"] = latest_record.prediction
        context["risk_factors"] = latest_record.risk_factors
        context["sleep_score"] = latest_record.sleep_score
        context["date_recorded"] = latest_record.date_recorded
        context["bmi"] = latest_record.bmi_category
        context["physical_activity"] = latest_record.physical_activity
        context["sleep_quality"] = latest_record.sleep_quality
        context["stress_level"] = latest_record.stress_level
        context["heart_rate"] = latest_record.heart_rate
        context["bp_systolic"] = latest_record.bp_systolic
    return render(request, "sleepdetect/analytics_dashboard.html", context)

# ================================
# AI CHATBOT
# ================================
@login_required(login_url='login')
def ai_chatbot(request):
    if request.method == "GET":
        return render(request, "sleepdetect/chatbot.html")

    if request.method == "POST":
        user_message = request.POST.get("message", "").strip()
        if not user_message:
            return JsonResponse({"reply": "Please enter a message."})
        if not client:
            return JsonResponse({"reply": "The AI service is currently unavailable. Please check the API configuration."})

        latest_record = SleepPredictionRecord.objects.filter(user=request.user).order_by('-date_recorded').first()
        if latest_record:
            prediction = latest_record.prediction
            risk_factors = latest_record.risk_factors
        else:
            prediction = "Unknown"
            risk_factors = []
        
        if "chat_history" not in request.session:
            system_prompt = f"""
            You are a helpful, empathetic, and knowledgeable AI Sleep Health Assistant.
            The user just received an ML prediction regarding their sleep health.
            Current ML Prediction: {prediction}
            User's Risk Factors: {', '.join(risk_factors) if risk_factors else 'None identified'}
            Guidelines:
            - Be conversational, supportive, and natural.
            - Answer the user's questions based on their specific prediction and risk factors.
            - Provide actionable, evidence-based sleep hygiene tips when appropriate.
            - IMPORTANT: You are an AI, not a doctor. Always recommend consulting a healthcare professional for serious symptoms.
            - Keep your responses concise (under 3 paragraphs).
            """
            request.session["chat_history"] = [{"role": "system", "content": system_prompt}]

        chat_history = request.session["chat_history"]
        chat_history.append({"role": "user", "content": user_message})

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=chat_history,
                max_tokens=800,
                temperature=0.7
            )
            reply = response.choices[0].message.content.strip()
            chat_history.append({"role": "assistant", "content": reply})
            request.session["chat_history"] = chat_history
            request.session.modified = True 
            return JsonResponse({"reply": reply})

        except Exception as e:
            print(f"GROQ ERROR: {str(e)}")
            return JsonResponse({
                "reply": "I'm having a little trouble connecting to my brain right now. Please try asking again in a moment!"
            })
    return JsonResponse({"reply": "Invalid request method."})

# ================================
# CONTACT VIEW
# ================================
def contact_view(request):
    if request.method == "POST":
        user_name = request.POST.get("name")
        user_email = request.POST.get("email")
        user_message = request.POST.get("message")
        subject = f"New Contact Request from {user_name}"
        body = f"Name: {user_name}\nEmail: {user_email}\n\nMessage:\n{user_message}"
        try:
            send_mail(
                subject, body, settings.EMAIL_HOST_USER,  
                ['restsureai@gmail.com'], fail_silently=False,
            )
            messages.success(request, "Your message has been sent successfully!")
            return redirect("contact") 
        except Exception as e:
            messages.error(request, "An error occurred while sending your message. Please try again.")
            print(f"Email Error: {e}")
    return render(request, "sleepdetect/contact.html")
