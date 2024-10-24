# users/serializers.py

from rest_framework import serializers
from .models import TempUser, User, Tag, Location


class TempUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempUser
        fields = ['phone_number']


class OTPVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)
    type = serializers.BooleanField(required=True)





class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'location']


class TagSerializer(serializers.ModelSerializer):  # Use ModelSerializer for ease of use
    class Meta:
        model = Tag  # Specify the model
        fields = ['name']  # List the fields you want to serialize

    name = serializers.CharField(max_length=100)  # You don't need to define this again

    def create(self, validated_data):
        # Create and return a new Tag instance
        return Tag.objects.create(tag=validated_data['name'])


# Updated UserSerializer
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    tags = TagSerializer(many=True, read_only=True)  # Ensure tags is a list of TagSerializer
    locations = LocationSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'name', 'email', 'password', 'display_picture',
            'is_verified', 'is_active', 'tags', 'locations', 'profession',
            'about', 'facebook_url', 'instagram_url', 'linkedin_url', 'twitter_url'
        ]
        read_only_fields = ['is_verified', 'is_active']

    def create(self, validated_data):
        # Expect tags to be a list of dictionaries
        tags_data = validated_data.pop('tags', [])
        user = User.objects.create_user(password=validated_data.pop('password'), **validated_data)

        for tag_data in tags_data:
            tag_name = tag_data['tag']
            tag, created = Tag.objects.get_or_create(name=tag_name)
            user.tags.add(tag)

        return user

    def update(self, instance, validated_data):
        # Expect tags to be a list of dictionaries
        tags_data = validated_data.pop('tags', [])
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        # Clear and re-add tags
        instance.tags.clear()
        for tag_data in tags_data:
            tag_name = tag_data['tag']
            tag, created = Tag.objects.get_or_create(name=tag_name)
            instance.tags.add(tag)

        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['about', 'profession']


class SocialMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['facebook_url', 'instagram_url', 'linkedin_url', 'twitter_url']
