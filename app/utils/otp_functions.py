# ===== Functions to handle OTP generation and verification =====

import pyotp
from app import redis_client
from app.utils.sms import send_sms


# --- Generate OTP ---
def generate_otp(phone_number):
    # Generate OTP
    otp_secret = pyotp.random_base32()
    totp = pyotp.TOTP(otp_secret)
    otp = totp.now()

    # Store OTP in Redis with expiration time
    redis_client.setex(f"otp:{phone_number}", 300, otp)  # expires in 300 seconds

    try:
        # Send the OTP via SMS
        send_sms(phone_number, otp)
        return True
    except Exception as e:
        print(f"Error sending OTP: {e}")
        return False
