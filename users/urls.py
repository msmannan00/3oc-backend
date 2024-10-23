from django.urls import path
from .views import RegisterPhoneNumberView, VerifyOTPView, ResendOTPView, SaveUserDataView, user_detail_view, user_locations_view

urlpatterns = [
    path('register/', RegisterPhoneNumberView.as_view(), name='register_phone'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
    path('save-user/', SaveUserDataView.as_view(), name='save_user'),
    path('locations/', user_locations_view, name='user-locations'),
    path('data/', user_detail_view, name='user-detail'),
]
