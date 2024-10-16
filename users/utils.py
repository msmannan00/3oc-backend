# import pyotp
# import random
# import string
# import json
# from django.utils import timezone
# from django.conf import settings
# from django_redis import get_redis_connection
# from .models import User, Referral, Friendship
# from passlib.hash import pbkdf2_sha256
# import redis
# from django.conf import settings
# # Initialize Redis connection
# redis_client = redis.StrictRedis(
#     host=settings.REDIS_HOST,  # Use the Redis host from settings
#     port=settings.REDIS_PORT,  # Use the Redis port from settings
#     password=settings.REDIS_PASSWORD,
#     decode_responses=True  # Optional: Decodes responses using the default encoding (utf-8)
# )
#
# # Function to send SMS (placeholder)
# def send_sms(phone_number, otp):
#     # Implement your SMS sending logic here
#     # For example, integrate with Twilio or any other SMS provider
#     print(f"Sending OTP {otp} to phone number {phone_number}")
#
# # --- Generate OTP ---
# import random
# from .models import OTP
#
# def generate_otp(phone_number):
#     otp_code = str(random.randint(100000, 999999))  # Generate a 6-digit OTP
#     otp, created = OTP.objects.update_or_create(
#         phone_number=phone_number,
#         defaults={'otp': otp_code, 'is_verified': False, 'created_at': timezone.now()},
#     )
#     # Send OTP to phone_number via SMS or other methods
#     return otp_code
#
#
# # --- Generate Referral Code ---
# def generate_referral_code(user_id, length=6):
#     existing_code = redis_client.get(f"user_id_ref_code:{user_id}")
#     if existing_code:
#         return existing_code.decode()
#
#     while True:
#         referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
#         if not redis_client.exists(f"ref_code:{referral_code}"):
#             # Store the user_id with the referral code, set to expire if needed
#             redis_client.setex(f"ref_code:{referral_code}", 300, user_id)  # Adjust expiration as needed
#             redis_client.setex(f"user_id_ref_code:{user_id}", 300, referral_code)
#             break
#
#     return referral_code
#
# # --- Add Friend Data to Temp DB ---
# def add_friend_data_to_temp_db(user_unique_key, ref_code):
#     referred_by_user_id = redis_client.get(f"ref_code:{ref_code}")
#     if referred_by_user_id:
#         redis_client.set(f"ref_code_friend:{user_unique_key}", referred_by_user_id)
#
# # --- Handle Referral ---
# def handle_referral(user, referrer_id, ref_code):
#     referrer = User.objects.get(id=referrer_id)
#     Friendship.objects.create(user=user, friend=referrer)
#     Referral.objects.create(user=user, referrer=referrer, referral_code=ref_code)
#     # Clean up Redis data
#     redis_client.delete(f"ref_code_friend:{user.phone_number}")
#     redis_client.delete(f"user_id_ref_code:{referrer_id}")
#     redis_client.delete(f"ref_code:{ref_code}")
