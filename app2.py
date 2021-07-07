import os
import logging

from datetime import datetime

from weather_api import weather
from indoor_temp import get_indoor_temperature
from send_push import push
from dbman import db

CRED_DIR = os.path.expanduser("~")
api_key_file = "{0}/.openweatherapi.txt".format(CRED_DIR)
push_api_cred_file = "{0}/.openwindows_push_api.txt".format(CRED_DIR)
SCRIPT_EXC_DIR = os.path.dirname(os.path.realpath(__file__))
db_path = "{0}/tempdb.json".format(SCRIPT_EXC_DIR)
log_dir = f'{SCRIPT_EXC_DIR}/app.log'
LOCAL_ZIPCODE = "97477,us"
date = datetime.now()

print(db_path)


# Setup logging
logging.basicConfig(filename=log_dir, format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', level=logging.DEBUG)

# Get weather API credentials from disk
if os.path.isfile(api_key_file):
    with open(api_key_file, 'r') as f:
        WEATHER_API_KEY = f.readline().strip()
else:
    print(f"No API Credential file found. Expecting: {api_key_file} - Check README file for setup instuctions")
    logging.info(f"No API Credential file found. Expecting: {api_key_file} - Check README file for setup instuctions")
if not WEATHER_API_KEY:
    print(f"No API Credentials found in: {api_key_file} - Check README file for setup instuctions")
    logging.info(f"No API Credentials found in: {api_key_file} - Check README file for setup instuctions")

# Get push API credentials from disk
if os.path.isfile(push_api_cred_file):
    with open(push_api_cred_file, 'r') as f:
        creds = f.readlines()
    TOKEN = creds[0].strip().split(':')[1]
    USER = creds[1].strip().split(':')[1]
else:
    print(f"No API Credentials found in: {push_api_cred_file} - Check README file for setup instuctions")
    logging.info(f"No API Credentials found in: {push_api_cred_file} - Check README file for setup instuctions")



indoor_temp = round(float(get_indoor_temperature()['temperature']))
outdoor_temp = int(round((weather.WeatherMan(WEATHER_API_KEY, LOCAL_ZIPCODE)).temperature))

hour = int(date.strftime("%H"))
DEGREE_BUFFER = 2
message = f"Inside: {indoor_temp} || Outside: {outdoor_temp} || Outside Adjusted: {outdoor_temp - DEGREE_BUFFER}"

def get_time_boundary(h):
    '''
    Calculates if operation is happening in the in the morning or evening and returns if the windows should be open or closed.
    '''
    if h >= 8 and h <= 4:
        return "close"
    if h >= 17 and h <= 23:
        return "open"
    return "OOB"

def get_notification_lock_status(db):
    # manage the lockfile. Update it, or delete it if it's old.

    if db["notification_sent"]:
        print("Notification has already been sent.")
        logging.info("Notification has already been sent.")
        quit()
    else:
        return False


boundary = get_time_boundary(hour)
tempdb = db.get_db(db_path)

# Check if db tempratures need to be updated, if so update them.
if indoor_temp > tempdb['indoor_max_temp']:
    print('Indoor temp is higher than temp, in db. updating record.')
    tempdb['indoor_max_temp'] = indoor_temp
    dbman.write_database_to_disk(tempdb)
    tempdb = dbman.get_db()
if outdoor_temp > tempdb['outdoor_max_temp']:
    print('Outdoor temp is higher than temp, in db. updating record.')
    tempdb['outdoor_max_temp'] = outdoor_temp
    dbman.write_database_to_disk(tempdb)
    tempdb = dbman.get_db()

if boundary == "close":
    get_notification_lock_status(tempdb)
    if (outdoor_temp - DEGREE_BUFFER) >= indoor_temp:
        # close windows
        print(f"CLOSE WINDOWS! {message}")
        push.send(TOKEN, USER, f"CLOSE WINDOWS! {message}")
        print("Sent Close windows notification")
        logging.debug(f"Writing lock file - date: {date.strftime('%b %d, %Y')} status: {boundary}")
        tempdb['notification_sent'] = True
        db.dbman.write_database_to_disk()
    else:
        #log temp and do nothing
        print(message)
        print("It's colder outside, recommend doing nothing!")
        logging.info(message)
        logging.info("It's colder outside, recommend doing nothing!")


if boundary == "open":
    manage_lockfile(lock_file_location)
    if (outdoor_temp - DEGREE_BUFFER) <= indoor_temp:
        print(message)
        push.send(TOKEN, USER, f"OPEN WINDOWS {message}")
        print("Sent OPEN windows notification")
        logging.debug(f"Writing lock file - date: {date.strftime('%b %d, %Y')} status: {boundary}")

        with open(lock_file_location, 'w') as f:
            f.write(date.strftime("%b %d, %Y")+"\n")
            f.write(f"{boundary}\n")

    else:
        #log temp and do nothing
        print(message)
        print("It's WARMER outside, recommend doing nothing!")
        logging.info(message)
        logging.info("It's WARMER outside, recommend doing nothing!")

if boundary == "OOB":
        print("Not in operational boundary.")
        logging.info(f"OOB: {message}")
