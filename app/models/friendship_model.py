from app import db, ma
from datetime import datetime, timezone


# ========== FRIENDSHIP MODEL ==========
class Friendship(db.Model):
    # Define the table name
    __tablename__ = "friendships"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    def __init__(self, user_id=None, friend_id=None):
        self.user_id = user_id
        self.friend_id = friend_id


# ========== FRIENDSHIP MODEL SERIALIZATION ==========
class FriendshipSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Friendship
        include_fk = True
        load_instance = True
        sqla_session = db.session


friendship_schema = FriendshipSchema()
