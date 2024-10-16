# users/serializers.py

from rest_framework import serializers
from .models import TempUser, User, Tag


class TempUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempUser
        fields = ['phone_number']


class OTPVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    tags = serializers.CharField(write_only=True, required=False, help_text="Comma-separated tags")

    class Meta:
        model = User
        fields = ['id', 'phone_number', 'name', 'email', 'password', 'display_picture', 'tags', 'is_verified',
                  'is_active']
        read_only_fields = ['is_verified', 'is_active']

    def create(self, validated_data):
        tags_str = validated_data.pop('tags', '')
        user = User.objects.create_user(password=validated_data.pop('password'), **validated_data)
        if tags_str:
            tag_names = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                user.tags.add(tag)
        return user

    def update(self, instance, validated_data):
        tags_str = validated_data.pop('tags', '')
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        if tags_str:
            instance.tags.clear()
            tag_names = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                instance.tags.add(tag)

        return instance
