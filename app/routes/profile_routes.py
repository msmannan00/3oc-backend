from flask import jsonify, request
from app import app, db
from flask_jwt_extended import get_jwt_identity, jwt_required, create_access_token
from app.models.user_model import User, user_schema
from app.models.social_media_model import SocialMedia, social_media_schema
import cloudinary
import cloudinary.uploader
import cloudinary.api
from app.utils import referral

# Set the Cloudinary configuration
cloudinary.config(
    cloud_name=app.config["CLOUDINARY_CLOUD_NAME"],
    api_key=app.config["CLOUDINARY_API_KEY"],
    api_secret=app.config["CLOUDINARY_API_SECRET"],
)


# ========== GET USER PROFILE ==========
@app.route("/api/users/<int:user_id>/profile", methods=["GET"])
@jwt_required()
def get_user(user_id):
    # Fetch the user from the database
    user = User.query.get(user_id)

    # If user not found, return error message
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Only go forward if the user id in the jwt token matches the user id in the request
    if user.id != get_jwt_identity()["id"]:
        return jsonify({"message": "Unauthorized to access another profile"}), 401

    # If user is found, return user data
    user_json = user_schema.dump(user)

    # Fetch the social media accounts of the user
    social_accounts = SocialMedia.query.filter_by(user_id=user_id).all()
    social_accounts_json = social_media_schema.dump(social_accounts, many=True)

    # Add the social media accounts to the user data
    user_json["socials"] = social_accounts_json

    # Return user data
    return jsonify({"message": "User found successfully.", "user": user_json}), 200


# ========== UPDATE USER PROFILE ==========
@app.route("/api/users/<int:user_id>/profile", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    user = User.query.get(user_id)
    print(user)

    # If user not found, return error message
    if user.id != get_jwt_identity()["id"]:
        return jsonify({"message": "Unauthorized to access another profile"}), 401

    # Get the user data from the request
    user_data = request.form.to_dict()

    # Update the user data
    user.profile_name = user_data.get("profile_name", user.profile_name)
    user.email = user_data.get("email", user.email)
    user.phone_number = user_data.get("phone_number", user.phone_number)

    # Update the profile picture
    if "profile_picture" in request.files:
        file = request.files["profile_picture"]
        if file.filename != "":
            # Delete the existing profile picture from Cloudinary unless it is the default image
            if (
                user.profile_picture
                != f"https://res.cloudinary.com/{app.config['CLOUDINARY_CLOUD_NAME']}/image/upload/default_profile_pic.avif"
            ):
                public_id = user.profile_picture.split("/")[-1].split(".")[0]
                cloudinary.uploader.destroy(public_id)

            # Upload the file to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file, public_id=f"user_{user.id}_profile_pic"
            )
            user.profile_picture = upload_result.get("secure_url")

    # Delete existing social media records
    SocialMedia.query.filter_by(user_id=user_id).delete()

    # Add new social media records from the request
    for key, value in user_data.items():
        if key.startswith("socials["):
            platform = key[len("socials[") : -1]  # Extract platform name
            new_social_media = SocialMedia(
                user_id=user_id, platform_name=platform, url=value
            )
            db.session.add(new_social_media)

    # Commit the changes to the database
    db.session.commit()

    return jsonify({"message": "User profile updated successfully"}), 200


# ========== GENERATE AN OTP FOR THE USER ==========
@app.route("/api/users/<int:user_id>/generate-referral-code", methods=["GET"])
@jwt_required()
def get_referral_code(user_id):
    # Check if the user accessing the code is right
    user_token_id = get_jwt_identity()["id"]

    if user_id != user_token_id:
        return ({"message": "Cannot access someone else's code"}), 401

    try:
        # Generate a unique referral code for a user
        ref_code = referral.generate_referral_code(user_id)
    except Exception as e:
        return (
            jsonify({"message": "Error generating referral code", "error": str(e)}),
            500,
        )

    # Check if that referral code exists in the redis database already
    return (
        jsonify({"message": "Referral code generated.", "referral_code": ref_code}),
        200,
    )


# ========== USER PROFILE VERIFICATION ROUTE ==========
@app.route("/api/users/<int:user_id>/verification", methods=["PUT"])
@jwt_required()
def verify_user(user_id):
    # Fetching the user details using the user id
    user = User.query.get(user_id)

    # Check if the user exists
    if user is None:
        return {"message": "User not found"}, 404

    # Check if a picture and id was received from the frontend
    if "picture" not in request.form.to_dict() or "id" not in request.files:
        return {"message": "All files were not sent"}, 400

    # image = request.files['image']
    # pdf = request.files['pdf']

    # If the files are there, update the user and verify them
    user.is_verified = True
    db.session.commit()

    # Create a new access token
    user_json = user_schema.dump(user)
    access_token = create_access_token(identity=user_json)

    return {"message": "User has been verified.", "access_token": access_token}
