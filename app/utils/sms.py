# ===== Functions to help with SMS operations =====

from app import account_sid, auth_token, twilio_phone_number, db
from twilio.rest import Client
from app.models.sms_logs_model import SMS_Logs


# --- SEND SMS TO USER ---
def send_sms(phone_number, otp=None, irl_id=None, user_id=None):
    try:
        # Send OTP via SMS using Twilio
        client = Client(account_sid, auth_token)

        # Send the OTP to the user's phone number
        message = None

        if otp is None:
            message = client.messages.create(
                body=f"Are you okay? Respond with a 'Yes' or 'No'.",
                from_=twilio_phone_number,
                to=phone_number,
            )

            # Record this in the sms logs
            sms_logs = SMS_Logs(account_sid, user_id, irl_id)
            db.session.add(sms_logs)
            db.session.commit()

        else:
            message = client.messages.create(
                body=f"Your 3oC OTP is: {otp}", from_=twilio_phone_number, to=phone_number
            )

        # Return the message SID
        return message.sid

    except Exception as e:
        print(f"Error sending OTP: {e}")
        return None
