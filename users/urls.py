from django.urls import path
from .views import (
    RegisterUserView,
    LoginUserView,
    OTPVerifyView,
    UpdatePhoneNumberView,
    ResendOTPView,
    GoogleAuthView
)

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register_user'),
    path('login/', LoginUserView.as_view(), name='login_user'),
    path('verify-otp/', OTPVerifyView.as_view(), name='verify_otp'),
    path('<int:user_id>/phone-number/', UpdatePhoneNumberView.as_view(), name='update_phone_number'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
    path('auth/google/', GoogleAuthView.as_view(), name='google_auth'),
]
