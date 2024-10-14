# 3ofCups Backend Web Service

This backend API serves as the core engine for the Three of Cups web application.

<p align="center">
  <img src="./assets/logo.png" alt="3oC Logo">
</p>

## Technologies, Libraries and APIs used

- [aiohttp](https://docs.aiohttp.org/en/stable/)
- [APScheduler](https://apscheduler.readthedocs.io/en/stable/)
- [Authlib](https://docs.authlib.org/en/latest/)
- [cloudinary](https://cloudinary.com/documentation)
- [Flask](https://flask.palletsprojects.com/en/2.0.x/)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- [PyOTP](https://github.com/pyauth/pyotp)
- [Twilio](https://www.twilio.com/docs/usage/api)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [redis](https://redis.io/documentation)
- [cloudinary](https://cloudinary.com/documentation)

## How to run this project locally

1. Clone this repository on your computer.
2. Create a Python3 Virtual environment. **Note:** You should have Python3 installed on your computer to run this backend API.
    ```bash
    python3 -m venv venv
    ```
3. Activate the virtual environment.
    ```bash
    source venv/bin/activate
    ```
4. Install all the required dependencies.
    ```bash
    pip install -r requirements.txt
    ```
5. Run the server by running the following command from the root of your project folder.
    ```bash
    python3 run.py
    ```

Your API should now be up and running at http://localhost:8000. You can check if the API is running by entering http://localhost:8000/api in your browser. If the API is running, you should see the message `{"message":"API runs successfully"}`.

## Author
[Aryan Khurana](https://github.com/AryanK1511)
