from app import db
from datetime import datetime, timezone


# ========== SMS LOGS MODEL ==========
class SMS_Logs(db.Model):
    # Define the table name
    __tablename__ = "sms_logs"

    id = db.Column(db.Integer, primary_key=True)
    twilio_sid = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    irl_id = db.Column(db.Integer, db.ForeignKey("irls.id"), nullable=False)
    reply_received = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    def __init__(self, twilio_sid=None, user_id=None, irl_id=None):
        self.twilio_sid = twilio_sid
        self.user_id = user_id
        self.irl_id = irl_id
