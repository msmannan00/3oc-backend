from flask import jsonify, request
from app import app, db
from app.models.user_model import User, user_schema
from app.models.friendship_model import Friendship
from flask_jwt_extended import jwt_required, get_jwt_identity


# ========== ADD FRIEND ROUTE ==========
@app.route("/api/friends/<int:user_id>/add-friend/<int:friend_id>", methods=["POST"])
@jwt_required()
def add_friend(user_id, friend_id):
    # Check if the user accessing the code is right
    user_token_id = get_jwt_identity()["id"]
    if user_id != user_token_id:
        return ({"message": "Unauthorized"}), 401

    if user_id == friend_id:
        return jsonify({"message": "Cannot add yourself as a friend"}), 400

    # Check if the friendship exists
    existing_friendship = Friendship.query.filter_by(
        user_id=user_id, friend_id=friend_id
    ).first()
    if existing_friendship:
        return jsonify({"message": "Already friends"}), 409

    # Create the friendship
    new_friendship = Friendship(user_id=user_id, friend_id=friend_id)

    try:
        db.session.add(new_friendship)
        db.session.commit()
        return jsonify({"message": "Friend added successfully"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error adding friend", "error": str(e)}), 500


# ========== REMOVE FRIEND ROUTE ==========
@app.route(
    "/api/friends/<int:user_id>/remove-friend/<int:friend_id>", methods=["DELETE"]
)
@jwt_required()
def remove_friend(user_id, friend_id):
    # Check if the user accessing the code is right
    user_token_id = get_jwt_identity()["id"]
    if user_id != user_token_id:
        return ({"message": "Unauthorized"}), 401

    # Check if the user is trying to remove themselves
    if user_id == friend_id:
        return jsonify({"message": "Cannot remove yourself as a friend"}), 400

    # Check if the friendship exists
    existing_friendship = Friendship.query.filter_by(
        user_id=user_id, friend_id=friend_id
    ).first()
    if not existing_friendship:
        return jsonify({"message": "Not friends"}), 404

    try:
        # Remove the friendship
        db.session.delete(existing_friendship)
        db.session.commit()
        return jsonify({"message": "Friend removed successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error removing friend", "error": str(e)}), 500


# ========== GET FRIENDS ROUTE ==========
@app.route("/api/friends/<int:user_id>", methods=["GET"])
@jwt_required()
def get_friends(user_id):
    # Check if the user accessing the code is right
    user_token_id = get_jwt_identity()["id"]
    if user_id != user_token_id:
        return ({"message": "Unauthorized"}), 401

    # Fetch friendships where the user is either the user or the friend
    friendships = Friendship.query.filter(
        (Friendship.user_id == user_id) | (Friendship.friend_id == user_id)
    ).all()

    # Collect the user IDs of the friends
    friend_ids = set()
    for friendship in friendships:
        # Add the friend's ID, checking whether the user is the user_id or the friend_id in the relationship
        if friendship.user_id == user_id:
            friend_ids.add(friendship.friend_id)
        else:
            friend_ids.add(friendship.user_id)

    # Fetch the user details of all friends
    friends = User.query.filter(User.id.in_(friend_ids)).all()

    # Serialize the friends
    friends = user_schema.dump(friends, many=True)

    return jsonify({"message": "Friends fetched successfully", "friends": friends}), 200
