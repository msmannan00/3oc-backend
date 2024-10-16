# users/serializers.py

from rest_framework import serializers
from .models import TempUser, User

class TempUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempUser
        fields = ['phone_number']

class OTPVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['pk', 'phone_number', 'name', 'email', 'display_picture', 'password', 'is_verified', 'is_active']
        read_only_fields = ['is_verified', 'is_active']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user
