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

# Convert string to datetime object
def string_to_datetime(time_string):
    
    # The format of the string
    time_format = "%I%p %Z"

    # Convert the string to a datetime object
    time_object = datetime.strptime(time_string, time_format)

    return(time_object)


# Checks whether string translates to valid datetime object
def check_time_format(time_string):
    try:
        time_format = "%I%p %Z"
        time_object = datetime.strptime(time_string, time_format)
        return True
    except ValueError:
        try:
            time_format = "%I%p %Z"
            time_object = datetime.strptime(time_string, time_format)
            time_zone = time_object.strftime('%Z')
            if time_zone in pytz.all_timezones:
                return True
            else:
                return False
        except ValueError:
            return False
        
def date_to_datetime(date_string):
    try:
        year = datetime.datetime.now().year
        start_date, end_date = date_string.split("-")
        start_date_object = datetime.datetime.strptime(f'{year} {start_date}', '%Y %b %d')
        end_date_object = datetime.datetime.strptime(f'{year} {end_date}', '%Y %b %d')
        start_date_object = pytz.utc.localize(start_date_object)
        end_date_object = pytz.utc.localize(end_date_object)
        return start_date_object,end_date_object
    except ValueError:
        return False