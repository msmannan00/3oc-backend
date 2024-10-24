from decouple import config
from twilio.rest import Client
import random
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import *
from .serializers import *
from django.db import IntegrityError, transaction
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model

User = get_user_model()  # Get the User model

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
        phone_number = request.data.get('phone_number')

        if not phone_number:
            return Response({'error': 'Phone number is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the phone number exists in the Registered Users table
        user = User.objects.filter(phone_number=phone_number).first()

        if user:
            # User is registered, generate OTP for sign-in
            otp = generate_otp()

            # Send OTP to the user's phone
            try:
                twilio_client.messages.create(
                    body=f"Your OTP code is: {otp}",
                    from_=TWILIO_PHONE_NUMBER,
                    to=phone_number
                )
                # Save the OTP in the User model
                user.otpCode = otp
                user.save(update_fields=['otpCode'])
                return Response({'message': 'OTP sent to your phone for sign-in.', 'user_type': False},
                                status=status.HTTP_200_OK)
            except Exception:
                return Response({'error': 'Failed to send OTP. Please try again later.'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # If the user does not exist, check the TempUser table
        temp_user = TempUser.objects.filter(phone_number=phone_number).first()

        if temp_user:
            # Phone number exists in TempUser, resend the OTP
            otp = temp_user.otp  # Resend the same OTP
            try:
                twilio_client.messages.create(
                    body=f"Your OTP code is: {otp}",
                    from_=TWILIO_PHONE_NUMBER,
                    to=phone_number
                )
                return Response({'message': 'OTP resent to your phone.', 'user_type': True}, status=status.HTTP_200_OK)
            except Exception:
                return Response({'error': 'Failed to send OTP. Please try again later.'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Phone number is not found in TempUser table, generate new OTP for sign-up
        otp = generate_otp()
        # Insert phone number and OTP into TempUser table
        TempUser.objects.create(
            phone_number=phone_number,
            otp=otp,
            is_verified=False
        )

        # Send OTP to the user's phone
        try:
            twilio_client.messages.create(
                body=f"Your OTP code is: {otp}",
                from_=TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            return Response({'message': 'OTP sent to your phone for sign-up.', 'user_type': True},
                            status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Failed to send OTP. Please try again later.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyOTPView(APIView):
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)

        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            otp = serializer.validated_data['otp']
            request_type = serializer.validated_data.get('type')

            if request_type is False:  # Verify for sign-in
                user = User.objects.filter(phone_number=phone_number).first()
                if not user or user.otpCode != otp:
                    return Response({'error': 'Invalid OTP or phone number not found.'},
                                    status=status.HTTP_400_BAD_REQUEST)

                # OTP matched, proceed with authentication (generate token)
                token, created = Token.objects.get_or_create(user=user)
                return Response({'message': 'OTP verified successfully.', 'token': token.key},
                                status=status.HTTP_200_OK)

            elif request_type is True:  # Verify for sign-up
                temp_user = TempUser.objects.filter(phone_number=phone_number, otp=otp).first()
                if not temp_user:
                    return Response({'error': 'Invalid OTP or phone number not found.'},
                                    status=status.HTTP_400_BAD_REQUEST)

                # Mark TempUser as verified and create a User instance
                # user = User.objects.create(
                #     phone_number=temp_user.phone_number,
                #     # Include other fields from TempUser as needed
                # )
                # user.set_password('defaultpassword')  # Change to your logic
                # user.save()
                #
                # # Generate token for the new user
                # token, created = Token.objects.get_or_create(user=user)

                # Mark TempUser as verified
                temp_user.is_verified = True
                temp_user.save()

                return Response({'message': 'OTP verified successfully for sign-up.'},
                                status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(APIView):
    def post(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({'error': 'Phone number is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Resend OTP logic for sign-in or sign-up
        otp = generate_otp()
        try:
            twilio_client.messages.create(
                body=f"Your OTP code is: {otp}",
                from_=TWILIO_PHONE_NUMBER,
                to=phone_number
            )
        except Exception:
            return Response({'error': 'Failed to send OTP. Please try again later.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Update or create OTP entry in TempUser table
        TempUser.objects.update_or_create(
            phone_number=phone_number,
            defaults={'otp': otp, 'is_verified': False}
        )

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

                    # Generate a token for the newly created user
                    token, created = Token.objects.get_or_create(user=user)

                return Response({
                    'message': 'User registered successfully.',
                    'token': token.key  # Return the token
                }, status=status.HTTP_201_CREATED)

            except IntegrityError:
                return Response({'error': 'User registration failed due to a unique constraint violation.'},
                                status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def user_locations_view(request):
    if request.method == 'GET':
        locations = Location.objects.filter(user=request.user)
        serializer = LocationSerializer(locations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = LocationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def user_detail_view(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


class AddTagAPIView(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user
        # Get all tags associated with the authenticated user
        tags = user.tags.all()
        # Serialize the tag names
        tag_names = [tag.name for tag in tags]
        return Response({"tags": tag_names}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        user = request.user
        tag_names = request.data.get('tag')

        if not tag_names:
            return Response({"error": "Tag name(s) are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Split the tag string by commas and remove any extra spaces
        tag_list = [tag.strip() for tag in tag_names.split(',') if tag.strip()]

        # Add each tag to the user
        added_tags = []
        for tag_name in tag_list:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            user.tags.add(tag)
            added_tags.append(tag_name)

        user.save()

        return Response({"message": "Tags added successfully", "tags": added_tags}, status=status.HTTP_201_CREATED)


class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SocialMediaLinksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = SocialMediaSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        serializer = SocialMediaSerializer(user, data=request.data, partial=True)  # Allow partial updates
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
