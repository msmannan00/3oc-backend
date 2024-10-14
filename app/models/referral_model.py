from app import db, ma
from datetime import datetime, timezone


# ========== REFERRAL MODEL ==========
class Referral(db.Model):
    # Define the table name
    __tablename__ = "referrals"

    id = db.Column(db.Integer, primary_key=True)
    got_referred = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    referred_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    ref_code = db.Column(db.String(6), nullable=True)

    def __init__(self, got_referred=None, referred_by=None, ref_code=None):
        self.got_referred = got_referred
        self.referred_by = referred_by
        self.ref_code = ref_code


# ========== REFERRAL MODEL SERIALIZATION ==========
class ReferralSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Referral
        include_fk = True
        load_instance = True
        sqla_session = db.session


referral_schema = ReferralSchema()
