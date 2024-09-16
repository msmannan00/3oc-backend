from apscheduler.util import undefined
from flask import jsonify, request
from app import app, db
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import json
from app.models.user_model import User, user_schema
from passlib.hash import pbkdf2_sha256
from app.utils import otp_functions, referral
from app import redis_client


# ========== CREATE A NEW USER ==========
@app.route("/api/users/register", methods=["POST"])
def register_user():
    try:
        # Get the user data from the request
        user_data = request.get_json()

        # Check if the user already exists based on whether the email or phone number already exists
        existing_user = User.query.filter(
            (User.email == user_data.get("email"))
            | (User.phone_number == user_data.get("phone_number"))
        ).first()
        if existing_user:
            return (
                jsonify(
                    {
                        "message": "An account with the same phone number or email already exists"
                    }
                ),
                400,
            )

        # Hash the password
        password_hash = pbkdf2_sha256.hash(user_data.get("password"))

        # Create a new user if the user doesn't exist already
        new_user = {
            "profile_name": user_data.get("profile_name"),
            "email": user_data.get("email"),
            "phone_number": user_data.get("phone_number"),
            "password": password_hash,
            "profile_picture": f"https://res.cloudinary.com/{app.config['CLOUDINARY_CLOUD_NAME']}/image/upload/default_profile_pic.avif",
        }

        # Save the user data in Redis temporarily instead of saving in the database
        redis_client.set(f"user_data:{user_data['phone_number']}", json.dumps(new_user))

        # Check if the user was referred
        ref_code = user_data.get("referral_code")

        # If yes, add the referral details in the redis database
        if ref_code:
            user_unique_key = user_data.get("phone_number")
            referral.add_friend_data_to_temp_db(user_unique_key, ref_code)

        # Generate OTP
        otp_functions.generate_otp(user_data.get("phone_number"))

        # Remove the password from the jwt token that we will create
        new_user.pop("password", None)

        # Create JWT token
        access_token = create_access_token(identity=new_user)

        # Return message
        return (
            jsonify(
                {
                    "message": "OTP generated and sent successfully. Please verify OTP to complete registration.",
                    "access_token": access_token,
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Unexpected error: {str(e)}")  # Log the error
        return jsonify({"error": "Server Error", "details": str(e)}), 500


# ========== LOGIN USER ==========
@app.route("/api/users/login", methods=["POST"])
def login_user():
    try:
        # Get the user data from the request
        user_data = request.get_json()

        # Extract user info from the request
        phone_number = user_data.get("phone_number")
        password = user_data.get("password")

        # Check if the user exists based on the email or phone number
        existing_user = User.query.filter((User.phone_number == phone_number)).first()
        if not existing_user:
            return jsonify({"message": "User does not exist"}), 400

        # Check if the password is correct
        if pbkdf2_sha256.verify(password, existing_user.password):
            # Check if the user was referred
            ref_code = user_data.get("referral_code")

            # Check to see whether the user was referred
            if ref_code is not None:
                user_unique_key = user_data.get("phone_number")
                referral.add_friend_data_to_temp_db(user_unique_key, ref_code)

                # Throw an error if the user is trying to refer themselves
                referrer_id = redis_client.get(f"ref_code_friend:{phone_number}")

                if str(existing_user.id) == str(referrer_id):
                    return jsonify({"message": "Cannot add yourself as friend."}), 400

            # Generate OTP and send to user's phone for additional verification
            otp_functions.generate_otp(phone_number)

            # Create JWT token
            existing_user_json = user_schema.dump(existing_user)
            access_token = create_access_token(identity=existing_user_json)

            return (
                jsonify({"message": "Login Successful", "access_token": access_token}),
                201,
            )
        else:
            return jsonify({"message": "Incorrect number or password"}), 400

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Unexpected error: {str(e)}")  # Log the error
        return jsonify({"error": "Server Error", "details": str(e)}), 500


# ========== VERIFY OTP FOR SIGNUP AND LOGIN ==========
@app.route("/api/users/verify-otp", methods=["POST"])
@jwt_required()
def verify_otp():
    # Fetching the user's data from the front end
    data = request.get_json()
    phone_number = data.get("phone_number")
    user_otp = data.get("otp")
    action = None

    # Validate input
    if not phone_number or not user_otp:
        return jsonify({"error": "Missing phone number or OTP"}), 400

    # Get the stored OTP from Redis
    stored_otp = redis_client.get(f"otp:{phone_number}")

    if not stored_otp == user_otp:
        return jsonify({"error": "Invalid OTP"}), 401

    # Attempt to retrieve existing user or user data from Redis
    existing_user = User.query.filter_by(phone_number=phone_number).first()
    user_data_json = redis_client.get(f"user_data:{phone_number}")
    user_data = json.loads(user_data_json) if user_data_json else None

    # Determine if this is a new registration or a login
    if existing_user:
        user_json = user_schema.dump(existing_user)
        action = "login"
    elif user_data:
        new_user = User(**user_data)
        db.session.add(new_user)
        db.session.commit()
        user_json = user_schema.dump(new_user)
        action = "registration"
    else:
        return (
            jsonify({"error": "User not found and no registration data available"}),
            404,
        )

    # Handle referrals if applicable
    # Get the friend that referred the user from redis
    referrer_id = redis_client.get(f"ref_code_friend:{phone_number}")
    # Get the referral code of the referrer
    ref_code = redis_client.get(f"user_id_ref_code:{referrer_id}")
    if referrer_id and ref_code:
        referral.handle_referral(user_json["id"], phone_number, referrer_id, ref_code)

    # Clean up Redis data
    redis_client.delete(f"otp:{phone_number}")
    redis_client.delete(f"user_data:{phone_number}")

    # Create JWT token
    access_token = create_access_token(identity=user_json)

    return (
        jsonify(
            {
                "message": f"OTP verified, user {action} successful",
                "access_token": access_token,
            }
        ),
        201,
    )


# ========== UPDATE USER PHONE NUMBER ==========
@app.route("/api/users/<int:user_id>/phone-number", methods=["PUT"])
@jwt_required()
def generate_otp_for_new_phone_number(user_id):
    try:
        # Fetch the user from the database
        user = User.query.get(user_id)

        # If user not found, return error message
        if not user:
            return jsonify({"message": "User not found"}), 404

        # Only allow the user to update their own phone number
        if user.id != get_jwt_identity()["id"]:
            return jsonify({"message": "Unauthorized to update phone number"}), 401

        # Get the new phone number from the request
        user_data = request.get_json()
        new_phone_number = user_data.get("phone_number")

        # Generate OTP for the new phone number
        otp_functions.generate_otp(new_phone_number)

        # Update the user's phone number
        user.phone_number = new_phone_number

        # Commit the changes to the database
        db.session.commit()

        # Create JWT token from the updated user data
        user_json = user_schema.dump(user)
        access_token = create_access_token(identity=user_json)

        return (
            jsonify(
                {"message": "OTP generated successfully", "access_token": access_token}
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Unexpected error: {str(e)}")  # Log the error
        return jsonify({"error": "Server Error", "details": str(e)}), 500


# ========= RESEND OTP ==========
@app.route("/api/users/resend-otp", methods=["POST"])
@jwt_required()
def resend_otp():
    print("Hello")
    # Get the phone number from the request
    data = request.get_json()

    phone_number = data["phone_number"]
    
    # Generate and send a new OTP
    otp_functions.generate_otp(phone_number)

    return jsonify({"message": "New OTP sent successfully"}), 201


# ========== GOOGLE SETUP FOR LOGIN AND SIGNUP ==========
@app.route("/api/auth/google", methods=["POST"])
def google_login():
    try:
        # Get user data from the request
        print("ppppppppppp1", flush=True)
        user_data = request.get_json()

        print("ppppppppppp2", flush=True)
        # Extract user info from the request and create an object
        user_identity = {
            "profile_name": user_data.get("profile_name"),
            "email": user_data.get("email"),
            "profile_picture": user_data.get("profile_picture"),
        }

        print("ppppppppppp3", flush=True)
        # Check if the user already exists based on the email
        existing_user = User.query.filter(User.email == user_data.get("email")).first()
        if existing_user:
            print("ppppppppppp4", flush=True)
            existing_user_json = user_schema.dump(existing_user)

            print("ppppppppppp5", flush=True)
            # Check if the user was referred
            ref_code = user_data.get("referral_code")
            print("ppppppppppp55", flush=True)
            print(ref_code, flush=True)
            print(type(ref_code), flush=True)
            if ref_code is "undefined":
                ref_code = None
                print("ppppppppppp7755", flush=True)

            print("ppppppppppp55", flush=True)
            if ref_code:
                print("ppppppppppp56", flush=True)
                user_unique_key = user_data.get("email")
                print("ppppppppppp57", flush=True)
                referral.add_friend_data_to_temp_db(user_unique_key, ref_code)
                print("ppppppppppp58", flush=True)

            print("ppppppppppp6", flush=True)
            # Get the friend that referred the user from redis
            referrer_id = redis_client.get(f"ref_code_friend:{user_data.get('email')}")

            print("ppppppppppp7", flush=True)
            # Get the referral code of the referrer
            ref_code = redis_client.get(f"user_id_ref_code:{referrer_id}")
            if referrer_id and ref_code:
                referral.handle_referral(
                    existing_user.id, user_data.get("email"), referrer_id, ref_code
                )

            # Create JWT token
            print("ppppppppppp8", flush=True)
            access_token = create_access_token(identity=existing_user_json)

            return (
                jsonify(
                    {
                        "message": "Google login successful.",
                        "access_token": access_token,
                    }
                ),
                201,
            )
        else:
            print("xxxxxxxxxxx1", flush=True)
            # Create a new user
            new_user = User(**user_identity)
            print("xxxxxxxxxxx2", flush=True)

            # Save the new user to the database
            db.session.add(new_user)
            db.session.commit()
            print("xxxxxxxxxxx3", flush=True)

            new_user_json = user_schema.dump(new_user)
            print("xxxxxxxxxxx4", flush=True)

            # Check if the user was referred
            ref_code = user_data.get("referral_code")
            if ref_code:
                user_unique_key = user_data.get("email")
                referral.add_friend_data_to_temp_db(user_unique_key, ref_code)

            print("xxxxxxxxxxx5", flush=True)
            # Get the friend that referred the user from redis
            referrer_id = redis_client.get(f"ref_code_friend:{user_data.get('email')}")

            print("xxxxxxxxxxx6", flush=True)
            # Get the referral code of the referrer
            ref_code = redis_client.get(f"user_id_ref_code:{referrer_id}")
            if referrer_id and ref_code:
                referral.handle_referral(
                    new_user_json["id"], user_data.get("email"), referrer_id, ref_code
                )

            # Create JWT token
            print("xxxxxxxxxxx7", flush=True)
            access_token = create_access_token(identity=new_user_json)
            print("xxxxxxxxxxx8", flush=True)

            return jsonify(
                {"message": "Google Signin Successful.", "access_token": access_token}
            )

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Unexpected error: {str(e)}")  # Log the error
        return jsonify({"error": "Server Error", "details": str(e)}), 500
