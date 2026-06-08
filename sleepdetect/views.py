from django.shortcuts import render, redirect



# STEP 1 – BASIC DETAILS

def step1_basic(request):
    if request.method == "POST":
        request.session["age"] = int(request.POST["age"])
        request.session["gender"] = request.POST["gender"]
        request.session["occupation"] = request.POST["occupation"]
        request.session["sleep_duration"] = float(request.POST["sleep_duration"])
        request.session["daily_steps"] = int(request.POST["daily_steps"])
        return redirect("step2_bmi")

    return render(request, "sleepdetect/step1_basic.html")



# STEP 2 – BMI (same page result)

def step2_bmi(request):
    context = {}

    if request.method == "POST":
        weight = float(request.POST["weight"])
        height_cm = float(request.POST["height"])

        height_m = height_cm / 100
        bmi = round(weight / (height_m ** 2), 1)

        if bmi < 18.5:
            status, color, bmi_category = "Underweight", "warning", 0
        elif bmi < 25:
            status, color, bmi_category = "Healthy", "success", 1
        elif bmi < 30:
            status, color, bmi_category = "Overweight", "orange", 2
        else:
            status, color, bmi_category = "Obese", "danger", 3

        request.session["bmi_category"] = bmi_category

        context = {
            "bmi": bmi,
            "status": status,
            "color": color,
            "show_result": True
        }

    return render(request, "sleepdetect/step2_bmi.html", context)



# STEP 3 – PHYSICAL ACTIVITY

def step3_activity(request):
    if request.method == "POST":
        request.session["physical_activity"] = float(
            request.POST["physical_activity"]
        )
        return redirect("sleep_quality")

    return render(request, "sleepdetect/step3_activity.html")



# STEP 4 – SLEEP QUALITY

def sleep_quality(request):
    if request.method == "POST":
        request.session["sleep_quality"] = float(
            request.POST["sleep_quality"]
        )
        return redirect("stress_level")

    return render(request, "sleepdetect/sleep_quality.html")



# STEP 5 – STRESS LEVEL

def stress_level(request):
    if request.method == "POST":
        request.session["stress_level"] = float(
            request.POST["stress_level"]
        )
        return redirect("heart_rate")

    return render(request, "sleepdetect/stress_level.html")



# STEP 6 – HEART RATE

def heart_rate(request):
    if request.method == "POST":
        request.session["heart_rate"] = int(request.POST["heart_rate"])
        return redirect("blood_pressure")

    return render(request, "sleepdetect/heart_rate.html")



# STEP 7 – BLOOD PRESSURE

def blood_pressure(request):
    if request.method == "POST":
        request.session["bp_systolic"] = int(request.POST["bp_systolic"])
        return redirect("predict_result")

    return render(request, "sleepdetect/blood_pressure.html")


