from decouple import config
from twilio.rest import Client
import random
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import TempUser, User
from .serializers import TempUserSerializer, OTPVerificationSerializer, UserSerializer
from django.db import IntegrityError, transaction

# Twilio Credentials
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER')

# Initialize Twilio Client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def generate_otp():
    return str(random.randint(100000, 999999))

class RegisterPhoneNumberView(APIView):
    def post(self, request):
        request_type = request.data.get('type')
        phone_number = request.data.get('phone_number')

        # Convert request_type to an integer if it's not None
        try:
            request_type = int(request_type)
        except (TypeError, ValueError):
            return Response({'error': 'Invalid type. Type should be 0 for sign-in and 1 for sign-up.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Now, check if request_type is 0 or 1
        if request_type not in [0, 1]:
            return Response({'error': 'Invalid type. Type should be 0 for sign-in and 1 for sign-up.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not phone_number:
            return Response({'error': 'Phone number is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate OTP
        otp = generate_otp()

        if request_type == 0:  # Sign-in
            # Check if phone number exists in the User table
            user_exists = User.objects.filter(phone_number=phone_number).exists()
            if not user_exists:
                return Response({'error': 'Phone number not found. Please sign up first.'},
                                status=status.HTTP_404_NOT_FOUND)
            # Try sending OTP via Twilio
            try:
                twilio_response = twilio_client.messages.create(
                    body=f"Your OTP code is: {otp}",
                    from_=TWILIO_PHONE_NUMBER,
                    to=phone_number
                )
                # Save OTP in TempUser table only if Twilio response is successful
                TempUser.objects.update_or_create(
                    phone_number=phone_number,
                    defaults={'otp': otp, 'is_verified': False}
                )
                return Response({'message': 'OTP sent to your phone for sign-in.'}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': 'Failed to send OTP. Please try again later.'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif request_type == 1:  # Sign-up
            # Check if the phone number already exists in User table
            user_exists = User.objects.filter(phone_number=phone_number).exists()
            if user_exists:
                return Response({'error': 'Phone number is already registered. Please sign in.'},
                                status=status.HTTP_400_BAD_REQUEST)
            # Try sending OTP via Twilio
            try:
                twilio_response = twilio_client.messages.create(
                    body=f"Your OTP code is: {otp}",
                    from_=TWILIO_PHONE_NUMBER,
                    to=phone_number
                )
                # Save phone number in TempUser table only if Twilio response is successful
                TempUser.objects.update_or_create(
                    phone_number=phone_number,
                    defaults={'otp': otp, 'is_verified': False}
                )
                return Response({'message': 'OTP sent to your phone for sign-up.'}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': 'Failed to send OTP. Please try again later.'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class VerifyOTPView(APIView):
    def post(self, request):

        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            otp = serializer.validated_data['otp']
            temp_user = TempUser.objects.filter(phone_number=phone_number).first()
            if not temp_user:
                return Response({'error': 'Phone number not found. Please register first.'}, status=status.HTTP_404_NOT_FOUND)
            if temp_user.otp == otp:
                temp_user.is_verified = True
                temp_user.save()
                return Response({'message': 'OTP verified successfully.'}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendOTPView(APIView):
    def post(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({'error': 'Phone number is required.'}, status=status.HTTP_400_BAD_REQUEST)

        temp_user = TempUser.objects.filter(phone_number=phone_number).first()

        if temp_user:
            otp = generate_otp()
            temp_user.otp = otp
            temp_user.is_verified = False
            temp_user.save()
        else:
            otp = generate_otp()
            temp_user = TempUser.objects.create(
                phone_number=phone_number,
                otp=otp,
                is_verified=False
            )

        try:
            twilio_client.messages.create(
                body=f"Your OTP code is: {otp}",
                from_=TWILIO_PHONE_NUMBER,
                to=phone_number
            )
        except Exception as e:
            return Response({'error': 'Failed to send OTP. Please try again later.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': 'OTP resent to your phone.'}, status=status.HTTP_200_OK)

class SaveUserDataView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data.get('phone_number')
            temp_user = TempUser.objects.filter(phone_number=phone_number, is_verified=True).first()
            if not temp_user:
                return Response({'error': 'Phone number not verified.'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                with transaction.atomic():
                    user = serializer.save()
                    temp_user.delete()
                return Response({'message': 'User registered successfully.'}, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                if 'unique constraint' in str(e).lower():
                    return Response({'error': 'A user with this email or phone number already exists.'}, status=status.HTTP_400_BAD_REQUEST)
                return Response({'error': 'An error occurred while creating the user.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
