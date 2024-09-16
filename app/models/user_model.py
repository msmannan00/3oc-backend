from app import db, ma
from datetime import datetime, timezone


# ========== USER MODEL ==========
class User(db.Model):
    # Define the table name
    __tablename__ = "users"

    # Define the columns of the table, with the data types
    id = db.Column(db.Integer, primary_key=True)
    profile_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    password = db.Column(db.String(128), nullable=True)
    date_joined = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    profile_picture = db.Column(db.String(255))
    is_verified = db.Column(db.Boolean, default=False)

    def __init__(
        self,
        profile_name=None,
        email=None,
        phone_number=None,
        password=None,
        profile_picture=None,
    ):
        self.profile_name = profile_name
        self.email = email
        self.phone_number = phone_number
        self.password = password
        self.profile_picture = profile_picture


# ========== USER MODEL SERIALIZATION ==========
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        # Store everything except password
        exclude = ["password"]
        include_fk = True
        load_instance = True
        sqla_session = db.session


user_schema = UserSchema()
