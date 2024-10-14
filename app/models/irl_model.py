from app import db, ma
from datetime import datetime, timezone
from app.models.user_model import UserSchema
import pytz


# ========== IRL MODEL ==========
class IRL(db.Model):
    # Define the table name
    __tablename__ = "irls"

    # Define the columns of the table with the datatypes
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(500), nullable=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    time_from = db.Column(db.DateTime, nullable=False)
    time_to = db.Column(db.DateTime, nullable=False)
    place = db.Column(db.String(255), nullable=False)
    enable_live_location = db.Column(db.Boolean, nullable=True)
    enable_notifications = db.Column(db.Boolean, nullable=True)
    notification_time = db.Column(db.DateTime, nullable=True)
    irl_status = db.Column(db.String(20), default="scheduled")
    date_created = db.Column(db.DateTime, default=datetime.now(pytz.utc))
    notes = db.Column(db.String(1000), nullable=True)

    def __init__(
        self,
        organizer_id=None,
        label=None,
        time_from=None,
        time_to=None,
        place=None,
        enable_live_location=False,
        notification_time=None,
        enable_notifications=False,
        notes=None,
    ):
        self.organizer_id = organizer_id
        self.label = label
        self.time_from = time_from
        self.time_to = time_to
        self.place = place
        self.enable_live_location = enable_live_location
        self.notification_time = notification_time
        self.enable_notifications = enable_notifications
        self.notes = notes


# ========== IRL PARTICIPANTS MODEL ==========
class IRL_Participants(db.Model):
    # Define the table name
    __tablename__ = "irl_participants"

    # Define the columns of the table with the datatypes
    id = db.Column(db.Integer, primary_key=True)
    irl_id = db.Column(db.Integer, db.ForeignKey("irls.id"), nullable=True)
    participant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def __init__(self, irl_id=None, participant_id=None):
        self.irl_id = irl_id
        self.participant_id = participant_id


# ========== IRL CONTACTS MODEL ==========
class IRL_Contacts(db.Model):
    # Define the table name
    __tablename__ = "irl_contacts"

    # Define the columns of the table with the datatypes
    id = db.Column(db.Integer, primary_key=True)
    irl_id = db.Column(db.Integer, db.ForeignKey("irls.id"), nullable=True)
    contact_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def __init__(self, irl_id=None, contact_id=None):
        self.irl_id = irl_id
        self.contact_id = contact_id


# ========== IRL AND RELATED SCHEMAS ==========
class IRLParticipantSchema(ma.SQLAlchemyAutoSchema):
    participant = ma.Nested(UserSchema)

    class Meta:
        model = IRL_Participants
        include_fk = True


class IRLContactSchema(ma.SQLAlchemyAutoSchema):
    contact = ma.Nested(UserSchema)

    class Meta:
        model = IRL_Contacts
        include_fk = True


class IRLSchema(ma.SQLAlchemyAutoSchema):
    organizer = ma.Nested(UserSchema)
    participants = ma.Nested(IRLParticipantSchema, many=True)
    contacts = ma.Nested(IRLContactSchema, many=True)

    class Meta:
        model = IRL
