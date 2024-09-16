from datetime import datetime
import pytz

# Input UTC timestamp
utc_timestamp = "2024-05-04T17:01:00.000Z"
utc_time = datetime.strptime(utc_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")

# Convert to Toronto time
toronto_timezone = pytz.timezone("America/Toronto")
toronto_time = utc_time.astimezone(toronto_timezone)

print(toronto_time)
