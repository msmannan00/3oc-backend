from flask import jsonify, request
from app import app, db
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user_model import User
from app.models.irl_model import IRL, IRL_Participants, IRL_Contacts
from app.utils.irl import schedule_irl_jobs, cancel_scheduled_jobs, complete_irl, change_irl_status
from twilio.twiml.messaging_response import MessagingResponse
from app.models.sms_logs_model import SMS_Logs
from app import account_sid, auth_token, twilio_phone_number, db
from twilio.rest import Client


# ========== GET ALL THE IRLS FOR A USER ==========
@app.route("/api/users/<int:user_id>/scheduleIRL", methods=["GET"])
@jwt_required()
def get_irls(user_id):
    current_user_id = get_jwt_identity()["id"]

    # Check if it is the correct user
    if user_id != current_user_id:
        return jsonify({"message": "Unauthorized"}), 401

    try:
        # SQL query to fetch IRLs and related user details with all fields
        query = """
        SELECT irls.*, 
            org.id as org_id, org.profile_name as organizer_name, org.email as organizer_email, org.phone_number as organizer_phone, org.profile_picture as organizer_picture, org.is_verified as organizer_verified,
            part.id as part_id, part.profile_name as participant_name, part.email as participant_email, part.phone_number as participant_phone, part.profile_picture as participant_picture, part.is_verified as participant_verified,
            cont.id as cont_id, cont.profile_name as contact_name, cont.email as contact_email, cont.phone_number as contact_phone, cont.profile_picture as contact_picture, cont.is_verified as contact_verified
        FROM irls
        LEFT JOIN users as org ON irls.organizer_id = org.id
        LEFT JOIN irl_participants ON irls.id = irl_participants.irl_id
        LEFT JOIN users as part ON irl_participants.participant_id = part.id
        LEFT JOIN irl_contacts ON irls.id = irl_contacts.irl_id
        LEFT JOIN users as cont ON irl_contacts.contact_id = cont.id
        WHERE irls.organizer_id = :user_id OR part.id = :user_id OR cont.id = :user_id
        """

        # Fetch data from the database as per the query defined above
        irls = db.session.execute(query, {"user_id": user_id}).fetchall()

        # Dictionary to collect IRL information
        irl_dict = {}
        for row in irls:
            irl_id = row["id"]
            if irl_id not in irl_dict:
                irl_dict[irl_id] = {
                    "irl_id": irl_id,
                    "label": row["label"],
                    "time_from": row["time_from"],
                    "time_to": row["time_to"],
                    "place": row["place"],
                    "enable_live_location": row["enable_live_location"],
                    "enable_notifications": row["enable_notifications"],
                    "notification_time": row["notification_time"],
                    "irl_status": row["irl_status"],
                    "date_created": row["date_created"],
                    "notes": row["notes"],
                    "organizer": {
                        "id": row["org_id"],
                        "profile_name": row["organizer_name"],
                        "email": row["organizer_email"],
                        "phone": row["organizer_phone"],
                        "profile_picture": row["organizer_picture"],
                        "is_verified": row["organizer_verified"],
                    },
                    "participants": [],
                    "contacts": [],
                }
            # Ensure unique appending of participants and contacts
            participant = {
                "id": row["part_id"],
                "profile_name": row["participant_name"],
                "email": row["participant_email"],
                "phone": row["participant_phone"],
                "profile_picture": row["participant_picture"],
                "is_verified": row["participant_verified"],
            }
            contact = {
                "id": row["cont_id"],
                "profile_name": row["contact_name"],
                "email": row["contact_email"],
                "phone": row["contact_phone"],
                "profile_picture": row["contact_picture"],
                "is_verified": row["contact_verified"],
            }

            if (
                    participant not in irl_dict[irl_id]["participants"]
                    and participant["id"]
            ):
                irl_dict[irl_id]["participants"].append(participant)
            if contact not in irl_dict[irl_id]["contacts"] and contact["id"]:
                irl_dict[irl_id]["contacts"].append(contact)

        # Serialize and return the data
        return jsonify(
            {"message": "irls retrieved successfully.", "irls": list(irl_dict.values())}
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========== GET AN IRL ROUTE ==========
@app.route("/api/users/<int:user_id>/scheduleIRL/<int:irl_id>", methods=["GET"])
@jwt_required()
def get_specific_IRL(user_id, irl_id):
    current_user_id = get_jwt_identity()["id"]

    # Check if it is the correct user
    if user_id != current_user_id:
        return jsonify({"message": "Unauthorized"}), 401

    try:
        # SQL query to fetch IRLs and related user details with all fields
        query = """
        SELECT irls.*, 
            org.id as org_id, org.profile_name as organizer_name, org.email as organizer_email, org.phone_number as organizer_phone, org.profile_picture as organizer_picture, org.is_verified as organizer_verified,
            part.id as part_id, part.profile_name as participant_name, part.email as participant_email, part.phone_number as participant_phone, part.profile_picture as participant_picture, part.is_verified as participant_verified,
            cont.id as cont_id, cont.profile_name as contact_name, cont.email as contact_email, cont.phone_number as contact_phone, cont.profile_picture as contact_picture, cont.is_verified as contact_verified
        FROM irls
        LEFT JOIN users as org ON irls.organizer_id = org.id
        LEFT JOIN irl_participants ON irls.id = irl_participants.irl_id
        LEFT JOIN users as part ON irl_participants.participant_id = part.id
        LEFT JOIN irl_contacts ON irls.id = irl_contacts.irl_id
        LEFT JOIN users as cont ON irl_contacts.contact_id = cont.id
        WHERE irls.id = :irl_id
        """
        # Fetch data from the database as per the query defined above
        irls = db.session.execute(query, {"irl_id": irl_id}).fetchall()

        # Dictionary to collect IRL information
        irl_dict = {}
        for row in irls:
            irl_id = row["id"]
            if irl_id not in irl_dict:
                irl_dict[irl_id] = {
                    "irl_id": irl_id,
                    "label": row["label"],
                    "time_from": row["time_from"],
                    "time_to": row["time_to"],
                    "place": row["place"],
                    "notes": row["notes"],
                    "enable_live_location": row["enable_live_location"],
                    "enable_notifications": row["enable_notifications"],
                    "notification_time": row["notification_time"],
                    "irl_status": row["irl_status"],
                    "date_created": row["date_created"],
                    "organizer": {
                        "id": row["org_id"],
                        "profile_name": row["organizer_name"],
                        "email": row["organizer_email"],
                        "phone": row["organizer_phone"],
                        "profile_picture": row["organizer_picture"],
                        "is_verified": row["organizer_verified"],
                    },
                    "participants": [],
                    "contacts": [],
                }
            # Ensure unique appending of participants and contacts
            participant = {
                "id": row["part_id"],
                "profile_name": row["participant_name"],
                "email": row["participant_email"],
                "phone": row["participant_phone"],
                "profile_picture": row["participant_picture"],
                "is_verified": row["participant_verified"],
            }
            contact = {
                "id": row["cont_id"],
                "profile_name": row["contact_name"],
                "email": row["contact_email"],
                "phone": row["contact_phone"],
                "profile_picture": row["contact_picture"],
                "is_verified": row["contact_verified"],
            }

            if (
                    participant not in irl_dict[irl_id]["participants"]
                    and participant["id"]
            ):
                irl_dict[irl_id]["participants"].append(participant)
            if contact not in irl_dict[irl_id]["contacts"] and contact["id"]:
                irl_dict[irl_id]["contacts"].append(contact)

        # Serialize and return the data
        return jsonify(
            {"message": "irls retrieved successfully.", "irls": list(irl_dict.values())}
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========== UPDATE AN IRL ROUTE ==========
@app.route("/api/users/updateIRL/<int:irl_id>", methods=["PUT"])
@jwt_required()
def update_irl(irl_id):
    # Find the user and the IRL that we are trying to update
    current_user_id = get_jwt_identity()["id"]
    irl = IRL.query.filter_by(id=irl_id).first()

    # Return an error message if the IRL was not found
    if not irl:
        return jsonify({"message": "IRL not found"}), 404

    # Return an error if an unauth user tries to access this route
    if irl.organizer_id != current_user_id:
        return jsonify({"message": "Unauthorized to update this IRL"}), 403

    try:
        # Cancel existing scheduled jobs
        cancel_scheduled_jobs(irl_id)

        # Get the updated data from the request
        updated_data = request.get_json()

        # Update the IRL details
        irl.label = updated_data.get("irl_label", irl.label)
        irl.time_from = updated_data.get("time_from", irl.time_from)
        irl.time_to = updated_data.get("time_to", irl.time_to)
        irl.place = updated_data.get("place", irl.place)
        irl.enable_live_location = updated_data.get(
            "enable_live_location", irl.enable_live_location
        )
        irl.enable_notifications = updated_data.get(
            "enable_notifications", irl.enable_notifications
        )
        irl.notification_time = updated_data.get(
            "notification_time", irl.notification_time
        )
        irl.notes = updated_data.get("notes", irl.notes)

        # Update participants and contacts if provided
        if "connection_ids" in updated_data:
            # Remove existing participants
            IRL_Participants.query.filter_by(irl_id=irl_id).delete()
            # Add new participants
            for connection_id in updated_data["connection_ids"]:
                participant = IRL_Participants(
                    irl_id=irl_id, participant_id=connection_id
                )
                db.session.add(participant)

        client = Client(account_sid, auth_token)

        if "contact_ids" in updated_data:
            # Remove existing contacts
            IRL_Contacts.query.filter_by(irl_id=irl_id).delete()
            # Add new contacts
            for contact_id in updated_data["contact_ids"]:
                # Assigning empty list in case the key is not sent from the FE
                contact = IRL_Contacts(irl_id=irl.id, contact_id=contact_id)
                db.session.add(contact)

                cnt = User.query.get(contact_id)
                if not cnt:
                    continue

                organizer = User.query.get(irl.organizer_id)
                if not organizer:
                    continue

                message = client.messages.create(
                    body=f"You have been added as an emergency contact for {organizer.profile_name}. Open the app to see more details.",
                    from_=twilio_phone_number,
                    to=cnt.phone_number,
                )

        # Save the new updates
        db.session.commit()

        # Schedule new jobs if necessary
        if irl.enable_notifications:
            schedule_irl_jobs(
                irl_id=irl_id,
                run_date_from=irl.time_from,
                run_date_to=irl.time_to,
                enable_live_location=irl.enable_live_location,
                enable_notifications=irl.enable_notifications,
                notification_time=irl.notification_time,
            )

        return jsonify({"message": "IRL updated successfully!"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "A server error occurred.", "error": str(e)}), 500


# ========== PARTICIPANT WITHDRAWAL ==========
@app.route("/api/users/withdrawparticipant/<int:irl_id>", methods=["DELETE"])
@jwt_required()
def withdraw_participant(irl_id):
    try:
        # Get user data from the request
        user_data = request.get_json()

        # Find the participant entry for the user in the IRL
        participant = IRL_Participants.query.filter_by(
            participant_id=user_data["participant_id"], irl_id=irl_id
        ).first()

        if not participant:
            return jsonify({"message": "Participant not found in this IRL"}), 404

        # Fetch the IRL details
        irl = IRL.query.get(irl_id)

        # Notify the organizer
        organizer = User.query.get(irl.organizer_id)
        client = Client(account_sid, auth_token)

        # Assuming you have 'irl' and 'organizer' objects
        irl_id = irl.label if irl.label else str(irl.id)

        message = client.messages.create(
            body=f"Participant {participant.participant_id} has withdrawn from the IRL {irl_id}",
            from_=twilio_phone_number,
            to=organizer.phone_number
        )

        # Delete the participant entry
        db.session.delete(participant)
        db.session.commit()

        return jsonify({"message": "Participant successfully withdrawn"}), 200

    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"error": "Failed to withdraw participant", "details": str(e)}),
            500,
        )


# ========== CANCEL AN IRL ROUTE ==========
@app.route("/api/users/cancelIRL/<int:irl_id>", methods=["DELETE"])
@jwt_required()
def cancel_irl(irl_id):
    # Change the status of the IRL to cancelled
    # Cancel the jobs that are supposed to run for the notifications and changing job status
    current_user_id = get_jwt_identity()["id"]

    # Fetch the IRL entry from the database
    irl = IRL.query.filter_by(id=irl_id).first()

    if not irl:
        return jsonify({"message": "IRL not found"}), 404

    # Check if the user requesting the cancellation is the organizer or has permission
    if irl.organizer_id != current_user_id:
        return jsonify({"message": "Unauthorized to cancel this IRL"}), 403

    try:
        # Update the IRL status to canceled
        irl.irl_status = "canceled"
        db.session.commit()

        # Delete all SMS logs associated with this IRL
        sms_logs = SMS_Logs.query.filter_by(irl_id=irl_id).all()
        for log in sms_logs:
            db.session.delete(log)

        # Delete the IRL itself
        db.session.delete(irl)
        db.session.commit()

        # Cancel scheduled jobs
        cancel_scheduled_jobs(irl_id)

        return jsonify({"message": "IRL successfully canceled"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to cancel IRL", "details": str(e)}), 500


# ========== CREATE AN IRL ROUTE ==========
@app.route("/api/users/<int:user_id>/scheduleIRL", methods=["POST"])
@jwt_required()
def schedule_IRL(user_id):
    # Check if the user accessing the code is right
    user_token_id = get_jwt_identity()["id"]
    if user_id != user_token_id:
        return ({"message": "Unauthorized"}), 401

    # Fetch the user from the database
    user = User.query.get(user_id)

    # If user not found, return error message
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Get all the details that are sent from the frontend
    user_data = request.get_json()

    try:
        # Create a new IRL based on the data provided by the user
        irl = IRL(
            organizer_id=user_id,
            label=user_data.get("irl_label", None),
            time_from=user_data["time_from"],
            time_to=user_data["time_to"],
            place=user_data["place"],
            enable_live_location=user_data.get("enable_live_location", None),
            enable_notifications=user_data.get("enable_notifications", None),
            notification_time=(
                user_data.get("notification_time")
                if user_data.get("enable_notifications") is True
                else None
            ),
            notes=user_data.get("notes", None),
        )

        # Flush to get an ID and not store yet
        db.session.add(irl)
        db.session.flush()

        # Loop over the connection IDS and add them to the list of the people the meeting is set up with
        for connection_id in user_data.get(
                "connection_ids", []
        ):  # Assigning empty list in case the key is not sent from the FE
            participant = IRL_Participants(irl_id=irl.id, participant_id=connection_id)
            db.session.add(participant)

        client = Client(account_sid, auth_token)

        # Similarily, add all the contacts as well
        for contact_id in user_data.get(
                "contact_ids", []
        ):  # Assigning empty list in case the key is not sent from the FE
            contact = IRL_Contacts(irl_id=irl.id, contact_id=contact_id)
            db.session.add(contact)

            cnt = User.query.get(contact_id)
            if not cnt:
                continue

            message = client.messages.create(
                body=f"You have been added as an emergency contact for {user.profile_name}. Open the app to see more details.",
                from_=twilio_phone_number,
                to=cnt.phone_number,
            )

        db.session.commit()  # Commit all the changes

        # Schedule all jobs that are supposed to run once this meetup is created
        schedule_irl_jobs(
            irl_id=irl.id,
            run_date_from=user_data["time_from"],
            run_date_to=user_data["time_to"],
            enable_live_location=user_data.get("enable_live_location"),
            enable_notifications=user_data.get("enable_notifications"),
            notification_time=(
                user_data.get("notification_time")
                if user_data.get("enable_notifications") is True
                else None
            ),
        )

        return jsonify({"message": "IRL created successfully!"}), 201

    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        return jsonify({"message": "A server error occurred.", "error": str(e)}), 500


# ========== START AN IRL ROUTE ==========
@app.route("/api/users/startIRL/<int:irl_id>", methods=["PUT"])
@jwt_required()
def start_irl(irl_id):
    # Cancel the jobs that are supposed to run for the notifications and changing job status
    current_user_id = get_jwt_identity()["id"]

    # Get the name of the user who started the irl
    started_by = get_jwt_identity()['profile_name']

    # Fetch the IRL entry from the database
    irl = IRL.query.filter_by(id=irl_id).first()

    if not irl:
        return jsonify({"message": "IRL not found"}), 404

    # Check if the user requesting to start the IRL is the organizer or has permission
    if irl.organizer_id != current_user_id:
        return jsonify({"message": "Unauthorized to start this IRL"}), 403

    # If it is past the notification time, refuse to start the IRL.
    irl_started_after_notification_time = False
    if irl_started_after_notification_time:
        return jsonify({"message": "You cannot start the IRL after the notification time!"})

    try:
        client = Client(account_sid, auth_token)
        # Get all the contacts for the user
        contacts = IRL_Contacts.query.filter_by(irl_id=irl_id).all()

        # Update the IRL status to be in progress
        change_irl_status(irl_id, "in progress")

        # Message each contact
        for contact in contacts:
            contact_user = User.query.get(contact.contact_id)
            print(contact_user.phone_number)
            print(contact_user.profile_name)
            message = client.messages.create(
                body=f"{started_by} has started the IRL. Please stay tuned for further messages in case your friend needs you",
                from_=twilio_phone_number,
                to=contact_user.phone_number,
            )

        return jsonify({"message": "IRL successfully started"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to start IRL", "details": str(e)}), 500


# ========== END AN IRL ROUTE ==========
@app.route("/api/users/endIRL/<int:irl_id>", methods=["PUT"])
@jwt_required()
def end_irl(irl_id):
    # Change the status of the IRL to completed
    # Cancel the jobs that are supposed to run for the notifications and changing job status
    current_user_id = get_jwt_identity()["id"]

    # Fetch the IRL entry from the database
    irl = IRL.query.filter_by(id=irl_id).first()

    if not irl:
        return jsonify({"message": "IRL not found"}), 404

    # Check if the user requesting the cancellation is the organizer or has permission
    if irl.organizer_id != current_user_id:
        return jsonify({"message": "Unauthorized to end this IRL"}), 403

    try:
        # Update the IRL status to complete
        complete_irl(irl_id)

        # Get twilio client
        client = Client(account_sid, auth_token)

        # Get all the contacts for the user
        contacts = IRL_Contacts.query.filter_by(irl_id=irl_id).all()

        # Message each contact
        for contact in contacts:
            contact_user = User.query.get(contact.contact_id)
            print(contact_user.phone_number)
            print(contact_user.profile_name)
            message = client.messages.create(
                body=f"The IRL has ended and everything has gone well. Thank you for being a great friend!",
                from_=twilio_phone_number,
                to=contact_user.phone_number,
            )

        return jsonify({"message": "IRL successfully ended"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to end IRL", "details": str(e)}), 500


# ========== MESSAGE HANDLING ROUTE ==========
# This webhook is configured through the twilio console
@app.route("/api/message/handleUserReply", methods=["POST"])
def handle_user_reply():
    # Get the text reply that the user entered
    body = request.values.get("Body", None)
    reply = body.lower()

    # Only react to the message if you are looking for a response
    user_phone_number = request.form.get("From")
    user = User.query.filter_by(phone_number=user_phone_number).first()

    # Check if the user is in the sms logs
    user_sms_log = SMS_Logs.query.filter(
        SMS_Logs.user_id == user.id, SMS_Logs.reply_received == False
    ).first()

    # Start our TwiML response
    resp = MessagingResponse()

    # If the sms log was found then send the appropriate message based on the user's reply
    if user_sms_log:
        received = False
        if reply == "yes":
            resp.message("Glad to hear! Have fun 🙂")
            received = True

        elif reply == "no":
            resp.message("🚨 Alerting your buddies. Hang on!")

            # Get the IRL details for the message
            irl_id = user_sms_log.irl_id
            irl = IRL.query.get(irl_id)
            irl_notes = irl.notes if irl.notes else ""
            friend_name = user.profile_name

            # Get all the contacts for the user
            contacts = IRL_Contacts.query.filter_by(irl_id=irl_id).all()

            # Send OTP via SMS using Twilio
            client = Client(account_sid, auth_token)

            # Message each contact
            for contact in contacts:
                contact_user = User.query.get(contact.contact_id)
                print(contact_user.phone_number)
                print(contact_user.profile_name)
                message = client.messages.create(
                    body=f"{friend_name} needs you. \nCall {user.phone_number} right now. \n\n"
                         f"Notes for Backup Bud:\n {irl_notes}",
                    from_=twilio_phone_number,
                    to=contact_user.phone_number,
                )

            received = True

        user_sms_log.reply_received = received
        db.session.commit()

    return str(resp)
