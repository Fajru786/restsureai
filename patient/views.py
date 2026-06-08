from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def patient_dashboard(request):
    return render(request, 'patient/dashboard.html')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def profile_view(request):
    return render(request, "patient/profile.html")
