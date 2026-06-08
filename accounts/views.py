import random
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Profile

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect("/patient/dashboard/")
        
        messages.error(request, "Invalid username or password")

    return render(request, "accounts/login.html")

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("login")

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email") # NEW: Require email
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # Basic Validations
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect("register")
            
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered!")
            return redirect("register")

        # Generate a 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # Send OTP via Email
        subject = 'Verify Your Account'
        message = f'Your verification code is: {otp}'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]

        try:
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            
            # Temporarily store user data and OTP in the session
            request.session['temp_user_data'] = {
                'username': username,
                'email': email,
                'password': password,
                'otp': otp
            }
            
            messages.success(request, "An OTP has been sent to your email.")
            return redirect("verify_otp") # Redirect to the OTP entry page
            
        except Exception as e:
            messages.error(request, "Error sending email. Please check your email address and try again.")
            return redirect("register")

    return render(request, "accounts/register.html")

# NEW: View to handle OTP verification
def verify_otp_view(request):
    # Ensure there is temp data in the session
    if 'temp_user_data' not in request.session:
        messages.error(request, "Session expired. Please register again.")
        return redirect("register")

    if request.method == "POST":
        user_otp = request.POST.get("otp")
        session_data = request.session['temp_user_data']

        if user_otp == session_data['otp']:
            # OTP matches, create the user
            user = User.objects.create_user(
                username=session_data['username'],
                email=session_data['email'],
                password=session_data['password']
            )
            Profile.objects.create(user=user)

            # Clean up the session so data isn't lingering
            del request.session['temp_user_data']

            messages.success(request, "Registration successful! Please login.")
            return redirect("login")
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, "accounts/verify_otp.html")