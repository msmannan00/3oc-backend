# users/views.py

import random
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import TempUser, User, Tag
from .serializers import TempUserSerializer, OTPVerificationSerializer, UserSerializer
from django.db import IntegrityError, transaction

def generate_otp():
    return str(random.randint(100000, 999999))

class RegisterPhoneNumberView(APIView):
    def post(self, request):
        serializer = TempUserSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            otp = generate_otp()
            TempUser.objects.update_or_create(phone_number=phone_number, defaults={'otp': otp, 'is_verified': False})
            # TODO: Integrate with SMS service to send OTP
            print(f"Generated OTP for {phone_number}: {otp}")  # For debugging purposes
            return Response({'message': 'OTP sent to your phone.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        serializer = TempUserSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            temp_user = TempUser.objects.filter(phone_number=phone_number).first()
            if not temp_user:
                return Response({'error': 'Phone number not found. Please register first.'}, status=status.HTTP_404_NOT_FOUND)
            otp = generate_otp()
            temp_user.otp = otp
            temp_user.is_verified = False
            temp_user.save()
            # TODO: Integrate with SMS service to resend OTP
            print(f"Resent OTP for {phone_number}: {otp}")  # For debugging purposes
            return Response({'message': 'OTP resent to your phone.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
