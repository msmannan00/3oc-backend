from flask import Flask
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from config import Config
import redis
from authlib.integrations.flask_client import OAuth
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

# Create the Flask app
app = Flask(__name__)

# Initialize the Scheduler
scheduler = BackgroundScheduler(timezone=pytz.utc)

# Enable CORS for all domains on all routes
CORS(app, supports_credentials=True)

# Load the configuration
app.config.from_object(Config)

# Initialize JWTManager with the Flask app
jwt = JWTManager(app)

# Create the OAuth object
oauth = OAuth(app)

# Create a marshmallow object
ma = Marshmallow(app)

# Setup Redis connection using the configuration
redis_client = redis.StrictRedis(
    host=app.config["REDIS_HOST"],
    port=app.config["REDIS_PORT"],
    password=app.config["REDIS_PASSWORD"],
    decode_responses=True,
)

# Create the SQLAlchemy object
db = SQLAlchemy(app)

# Set up the Twilio client
account_sid = app.config["TWILIO_ACCOUNT_SID"]
auth_token = app.config["TWILIO_AUTH_TOKEN"]
twilio_phone_number = app.config["TWILIO_PHONE_NUMBER"]

# Import the routes
from app.routes import (
    user_routes,
    friendship_routes,
    profile_routes,
    test_routes,
    migration_route,
    irl_routes,
)
