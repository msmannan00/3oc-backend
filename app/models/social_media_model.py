from app import db, ma
from datetime import datetime, timezone


# ========== SOCIAL MEDIA MODEL ==========
class SocialMedia(db.Model):
    # Define the table name
    __tablename__ = "socials"

    # Define the columns of the table, with the data types
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    platform_name = db.Column(db.String(120), nullable=False)
    url = db.Column(db.String(500), nullable=True)

    def __init__(self, user_id=None, platform_name=None, url=None):
        self.user_id = user_id
        self.platform_name = platform_name
        self.url = url


# ========== SOCIAL MEDIA MODEL SERIALIZATION ==========
class SocialMediaSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = SocialMedia
        include_fk = True
        load_instance = True
        sqla_session = db.session


social_media_schema = SocialMediaSchema()
