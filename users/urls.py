from django.urls import path
from .views import RegisterPhoneNumberView, VerifyOTPView, ResendOTPView, SaveUserDataView

urlpatterns = [
    path('register/', RegisterPhoneNumberView.as_view(), name='register_phone'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
    path('save-user/', SaveUserDataView.as_view(), name='save_user'),
]
