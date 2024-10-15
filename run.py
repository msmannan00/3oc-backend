from dotenv import load_dotenv

# Load the env file
load_dotenv(dotenv_path=".env")

from config import Config
from app import app, db, scheduler

# Create all database tables before running the app
with app.app_context():
    db.create_all()

# Start the application
if __name__ == "__main__":
    scheduler.start()
    app.run(debug=True, port=8000, host="0.0.0.0")

