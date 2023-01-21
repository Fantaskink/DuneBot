from datetime import datetime
import pytz

def get_current_time():
    # Get the current date and time
    now = datetime.now()

    # Get the current timezone
    tz = pytz.timezone("UTC")

    # Localize the current date and time with the timezone
    local_time = tz.localize(now)
    return local_time

def is_past_datetime(target_datetime):
    if get_current_time() > target_datetime:
        return(True)
    else:
        return(False)