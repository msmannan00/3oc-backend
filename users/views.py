from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection
from django.conf import settings
from .models import User
import json
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
    OTPVerificationSerializer,
    UpdatePhoneNumberSerializer,
    GoogleAuthSerializer
)
from .utils import (
    generate_otp,
    redis_client,
    add_friend_data_to_temp_db,
    handle_referral,
    generate_referral_code
)
from rest_framework_simplejwt.tokens import RefreshToken
from passlib.hash import pbkdf2_sha256


# Helper function to get tokens
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh)
    }


# --- User Registration ---
class RegisterUserView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            # Hash the password using passlib (already handled by set_password)
            # Store user data in Redis temporarily
            user_data = {
                "profile_name": user.profile_name,
                "email": user.email,
                "phone_number": user.phone_number,
                "profile_picture": user.profile_picture,
            }
            redis_client.set(f"user_data:{user.phone_number}", json.dumps(user_data))
            # Handle referral if any
            ref_code = request.data.get("referral_code")
            if ref_code:
                add_friend_data_to_temp_db(user.phone_number, ref_code)
            # Generate OTP
            generate_otp(user.phone_number)
            # Generate JWT token
            tokens = get_tokens_for_user(user)
            return Response({
                "message": "OTP generated and sent successfully. Please verify OTP to complete registration.",
                "access_token": tokens['access'],
                "refresh_token": tokens['refresh']
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- User Login ---
class LoginUserView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            password = serializer.validated_data['password']
            referral_code = serializer.validated_data.get('referral_code')

            try:
                user = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                return Response({"message": "User does not exist"}, status=status.HTTP_400_BAD_REQUEST)

            if user.check_password(password):
                if referral_code:
                    add_friend_data_to_temp_db(phone_number, referral_code)
                    referrer_id = redis_client.get(f"ref_code_friend:{phone_number}")
                    if referrer_id and str(user.id) == referrer_id.decode():
                        return Response({"message": "Cannot add yourself as friend."},
                                        status=status.HTTP_400_BAD_REQUEST)
                # Generate OTP
                generate_otp(phone_number)
                tokens = get_tokens_for_user(user)
                return Response({
                    "message": "Login Successful",
                    "access_token": tokens['access'],
                    "refresh_token": tokens['refresh']
                }, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Incorrect number or password"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- OTP Verification ---
class OTPVerifyView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            otp_instance = serializer.validated_data['otp_instance']
            otp_instance.is_verified = True  # Mark OTP as verified
            otp_instance.save()
            return Response({"detail": "OTP verified successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# --- Update User Phone Number ---
class UpdatePhoneNumberView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, user_id):
        serializer = UpdatePhoneNumberSerializer(data=request.data)
        if serializer.is_valid():
            new_phone_number = serializer.validated_data['phone_number']
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            # Check if the requesting user is the same
            if user.id != request.user.id:
                return Response({"message": "Unauthorized to update phone number"}, status=status.HTTP_401_UNAUTHORIZED)
            # Generate OTP for new phone number
            generate_otp(new_phone_number)
            # Update phone number
            user.phone_number = new_phone_number
            user.save()
            # Generate new tokens
            tokens = get_tokens_for_user(user)
            return Response({
                "message": "OTP generated successfully",
                "access_token": tokens['access'],
                "refresh_token": tokens['refresh']
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- Resend OTP ---
class ResendOTPView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)
        # Generate and send new OTP
        if generate_otp(phone_number):
            return Response({"message": "New OTP sent successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed to send OTP"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- Google Authentication ---
class GoogleAuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if serializer.is_valid():
            profile_name = serializer.validated_data['profile_name']
            email = serializer.validated_data['email']
            profile_picture = serializer.validated_data.get('profile_picture')
            referral_code = serializer.validated_data.get('referral_code')
            try:
                user = User.objects.get(email=email)
                user_serializer = UserSerializer(user)
                # Handle referral
                if referral_code:
                    add_friend_data_to_temp_db(email, referral_code)
                referrer_id = redis_client.get(f"ref_code_friend:{email}")
                ref_code = redis_client.get(f"user_id_ref_code:{referrer_id.decode()}" if referrer_id else None)
                if referrer_id and ref_code:
                    handle_referral(user, int(referrer_id), ref_code.decode())
                tokens = get_tokens_for_user(user)
                return Response({
                    "message": "Google login successful.",
                    "access_token": tokens['access'],
                    "refresh_token": tokens['refresh']
                }, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                # Create new user
                user = User.objects.create(
                    profile_name=profile_name,
                    email=email,
                    phone_number='',
                    profile_picture=profile_picture or f"https://res.cloudinary.com/{settings.CLOUDINARY_CLOUD_NAME}/image/upload/default_profile_pic.avif",
                    is_verified=True
                )
                # Generate referral code if needed
                user_serializer = UserSerializer(user)
                if referral_code:
                    add_friend_data_to_temp_db(email, referral_code)
                referrer_id = redis_client.get(f"ref_code_friend:{email}")
                ref_code = redis_client.get(f"user_id_ref_code:{referrer_id.decode()}" if referrer_id else None)
                if referrer_id and ref_code:
                    handle_referral(user, int(referrer_id), ref_code.decode())
                tokens = get_tokens_for_user(user)
                return Response({
                    "message": "Google Signin Successful.",
                    "access_token": tokens['access'],
                    "refresh_token": tokens['refresh']
                }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
