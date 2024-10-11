from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from datetime import timedelta


class UserManager(BaseUserManager):
    def create_user(self, phone_number, profile_name, email=None, password=None, profile_picture=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number must be set')
        email = self.normalize_email(email)
        user = self.model(
            phone_number=phone_number,
            profile_name=profile_name,
            email=email,
            profile_picture=profile_picture,
            date_joined=timezone.now(),
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, profile_name, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, profile_name, email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    profile_name = models.CharField(max_length=120)
    email = models.EmailField(max_length=120, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, unique=True)
    profile_picture = models.URLField(max_length=255, blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)  # Required for Django admin
    is_staff = models.BooleanField(default=False)  # Required for Django admin

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['profile_name', 'email']

    objects = UserManager()

    def __str__(self):
        return self.phone_number

class Referral(models.Model):
    user = models.ForeignKey(User, related_name='referrals', on_delete=models.CASCADE)
    referrer = models.ForeignKey(User, related_name='referrals_made', on_delete=models.CASCADE)
    referral_code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} referred by {self.referrer}"

class Friendship(models.Model):
    user = models.ForeignKey(User, related_name='friendships', on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name='friends', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'friend')

    def __str__(self):
        return f"{self.user} is friends with {self.friend}"



class OTP(models.Model):
    phone_number = models.CharField(max_length=20)
    otp = models.CharField(max_length=6)  # 6 digits for OTP
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_valid(self):
        # Check if the OTP is valid for 5 minutes
        return timezone.now() <= self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"OTP {self.otp} for {self.phone_number}"