# ===== Functions to handle referral code creation and deletion =====

import string
import random
from app import redis_client, db
from app.models.friendship_model import Friendship
from app.models.referral_model import Referral


# Generate a Referral Code
def generate_referral_code(user_id, length=6):
    # Check if there is already a referral code for this phone number
    existing_code = redis_client.get(f"user_id_ref_code:{user_id}")
    if existing_code:
        return existing_code

    # Generate a unique referral code
    while True:
        characters = string.ascii_uppercase + string.digits
        referral_code = "".join(random.choice(characters) for _ in range(length))

        if not redis_client.exists(f"ref_code:{referral_code}"):
            # Store the phone number with the referral code, set to expire in 300 seconds (5 minutes)
            redis_client.setex(f"ref_code:{referral_code}", 300, user_id)
            # Store the referral code with the user ID, set to expire in 300 seconds (5 minutes)
            redis_client.setex(f"user_id_ref_code:{user_id}", 300, referral_code)
            break

    return referral_code


# Add a friend to the temporary database
def add_friend_data_to_temp_db(user_unique_key, ref_code):
    # Check which user does the ref_code belong to
    print("pppppppppppcccxzcxzccxzx1", flush=True)
    referred_by_user_id = redis_client.set("","")
    print("pppppppppppcccx1", flush=True)
    referred_by_user_id = redis_client.get(f"ref_code:{ref_code}")
    print("pppppppppppcccx1", flush=True)

    print("pppppppppppx2", flush=True)
    if referred_by_user_id:
        # Add the user to the list of friends of the referrer in the temporary DB
        print("pppppppppppx3", flush=True)
        redis_client.set(f"ref_code_friend:{user_unique_key}", referred_by_user_id)
        print("pppppppppppx4", flush=True)


# Handle a referral
def handle_referral(user_id, user_unique_key, referrer_id, ref_code):
    # Add the user to the friends list of the referrer
    new_friendship = Friendship(user_id, referrer_id)
    db.session.add(new_friendship)
    db.session.commit()

    # Record the referral in the database
    new_referral = Referral(user_id, referrer_id, ref_code)
    db.session.add(new_referral)
    db.session.commit()

    # Delete everything from the temporary database
    redis_client.delete(f"ref_code_friend:{user_unique_key}")
    redis_client.delete(f"user_id_ref_code:{referrer_id}")
    redis_client.delete(f"ref_code:{ref_code}")
