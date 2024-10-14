# ===== Functions related to irls =====

from app import db, scheduler
from app.models.irl_model import IRL
from app.models.user_model import User
from app.models.sms_logs_model import SMS_Logs
from app.utils.sms import send_sms


# --- SCHEDULE ALL JOBS ---
def schedule_irl_jobs(
    irl_id,
    run_date_from,
    run_date_to,
    enable_live_location=False,
    enable_notifications=False,
    notification_time=None,
):


    # Scheduling currently disabled. The irl is started when the user clicks SStart IRl.
    # # Schedule job to change the status to 'in progress' once the meetup starts
    # scheduler.add_job(
    #     func=change_irl_status,
    #     args=[irl_id, "in progress"],
    #     trigger="date",
    #     run_date=run_date_from,
    #     replace_existing=True,
    #     id=f"irl_status_change_{irl_id}_in_progress",
    # )

    # Currently disabled. The irl is set to complete when the user clicks on End IRL
    # # Schedule job to change the status to 'completed' once the meetup ends
    # scheduler.add_job(
    #     func=complete_irl,
    #     args=[irl_id],
    #     trigger="date",
    #     run_date=run_date_to,
    #     replace_existing=True,
    #     id=f"irl_status_change_{irl_id}_completed",
    # )

    # Schedule a job to send a message to the user at the time they want to send the message at
    if enable_notifications and notification_time is not None:
        scheduler.add_job(
            func=send_notification,
            args=[irl_id],
            trigger="date",
            run_date=notification_time,
            replace_existing=True,
            id=f"irl_notification_{irl_id}",
        )

    print(scheduler.get_jobs())


# --- DELETE SMS LOGS FOR COMPLETED IRL ---
def delete_sms_logs(irl_id):
    try:
        # Delete SMS logs for the given IRL ID
        SMS_Logs.query.filter_by(irl_id=irl_id).delete()
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error deleting SMS logs: {str(e)}")  # Add logging
        return False


# --- CHANGE THE IRL STATUS IN DATABASE ---
def change_irl_status(irl_id, status="scheduled"):
    try:
        irl = IRL.query.get(irl_id)
        irl.irl_status = status
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error changing status: {str(e)}")  # Add logging
        return False


# --- COMPLETE THE IRL AND DELETE SMS LOGS ---
def complete_irl(irl_id):
    try:
        # Change the status to 'completed'
        change_irl_status(irl_id, "completed")

        # Delete SMS logs for the completed IRL
        delete_sms_logs(irl_id)

        return True
    except Exception as e:
        print(f"Error completing IRL: {str(e)}")  # Add logging
        return False


# --- CANCEL ALL SCHEDULED JOBS ---
def cancel_scheduled_jobs(irl_id):
    job_ids = [
        "irl_status_change_{}_in_progress".format(irl_id),
        "irl_status_change_{}_completed".format(irl_id),
        "irl_notification_{}".format(irl_id),
    ]
    for job_id in job_ids:
        job = scheduler.get_job(job_id)
        if job:
            job.remove()

    print("Scheduled jobs for IRL ID {} have been cancelled.".format(irl_id))


# --- SEND USER A CHECK IN NOTIFICATION ---
def send_notification(irl_id):
    try:
        # Get the organizer ID using the IRL ID
        irl = IRL.query.get(irl_id)
        organizer_id = irl.organizer_id

        # Get the phone number of the organizer from the database using the ID
        user = User.query.get(organizer_id)
        phone_number = user.phone_number

        # Send user the message
        send_sms(phone_number=phone_number, user_id=organizer_id, irl_id=irl_id)

        return True
    except Exception as e:
        print(f"Error changing status: {str(e)}")  # Add logging
        return False
