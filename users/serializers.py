from rest_framework import serializers
from .models import User, Referral, Friendship, OTP
from django.contrib.auth.password_validation import validate_password

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password', 'is_staff', 'is_superuser', 'groups', 'user_permissions']
        read_only_fields = ['id', 'date_joined', 'is_verified']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    profile_picture = serializers.URLField(required=False)

    class Meta:
        model = User
        fields = ['id', 'profile_name', 'email', 'phone_number', 'password', 'profile_picture']

    def create(self, validated_data):
        user = User.objects.create_user(
            phone_number=validated_data['phone_number'],
            profile_name=validated_data['profile_name'],
            email=validated_data.get('email'),
            password=validated_data['password'],
            # profile_picture=validated_data.get('profile_picture', f"https://res.cloudinary.com/{self.context['request'].settings.CLOUDINARY_CLOUD_NAME}/image/upload/default_profile_pic.avif")
        )
        return user

class UserLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    referral_code = serializers.CharField(required=False, allow_blank=True)


class OTPVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    otp = serializers.CharField(required=True)

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        otp_code = attrs.get('otp')

        try:
            otp_instance = OTP.objects.get(phone_number=phone_number, otp=otp_code)
        except OTP.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP.")

        if not otp_instance.is_valid():
            raise serializers.ValidationError("OTP has expired.")

        attrs['otp_instance'] = otp_instance
        return attrs


class UpdatePhoneNumberSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)

class GoogleAuthSerializer(serializers.Serializer):
    profile_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    profile_picture = serializers.URLField(required=False)
    referral_code = serializers.CharField(required=False, allow_blank=True)
