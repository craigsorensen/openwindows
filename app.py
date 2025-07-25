import os
import logging
from datetime import datetime
from weather_api import weather
from indoor_temp import get_indoor_temperature
from send_push import push
from dbman import db

#### Define paths and file locations

#where cred files are located
CRED_DIR = os.path.expanduser("~")
## Weatherapi key file
#api_key_file = "{0}/.openweatherapi.txt".format(CRED_DIR)
api_key_file = "{0}/.config/.weatherapi.txt".format(CRED_DIR)
# Pushover cred file
push_api_cred_file = "{0}/.openwindows_push_api.txt".format(CRED_DIR)
# Detect script execution directory
SCRIPT_EXC_DIR = os.path.dirname(os.path.realpath(__file__))
# Temperature DB file location
db_path = "{0}/tempdb.json".format(SCRIPT_EXC_DIR)
# Log file location
log_dir = f"{SCRIPT_EXC_DIR}/app.log"

### Random important variables
# Weather location for use with Open Weather API
#LOCAL_ZIPCODE = "97477,us"
# Weather location for use with WeatherAPI.com
LOCAL_ZIPCODE = "97477"

# Date and formatted date
date = datetime.now()
pretty_date = date.strftime("%b-%d-%Y") #Nov-01-2021

# used to compensate for opening windows when it's still too warm outside. This works by taking the outside
# temperature and subtracting the OUTSIDE_DEGREE_BUFFER. Then using that value for logic. Set to 0 to disable buffer.
OUTSIDE_DEGREE_BUFFER = 2

# use these two values for tuning the open window logic:

# used to set the open window trigger point. Ouside temp must reach at least OUTIDE_DEGREE_TRIGGER degrees
OUTSIDE_DEGREE_TRIGGER = 80
# used to set the difference between outside and inside temp delta as a secondary trigger.
# outside temp must be at least DEGREE_DELTA higher than inside temp
DEGREE_DELTA = 5

# Setup logging
logging.basicConfig(filename=log_dir, format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', level=logging.DEBUG)

print(f"log file: {log_dir}")
print(f"DB Path: {db_path}")
logging.debug(f"DB Path: {db_path}")

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
message = f"Inside: {indoor_temp} || Outside: {outdoor_temp} || Outside Adjusted: {outdoor_temp - OUTSIDE_DEGREE_BUFFER}"
logging.info(message)
print(message)

def get_time_boundary(h):
    '''
    Calculates if operation is happening in the morning or evening and returns if the windows should be open or closed.
    '''
    if 6 <= h < 14:  # Morning: 6 AM to 1:59 PM
        return "close"
    if 18 <= h < 24:  # Evening: 6 PM to 11:59 PM
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
dbman = db.db_manager(db_path)

print("Checking if temperature db exists..")
logging.debug("Checking if temperature db exists..")
if(dbman.check_if_db_file_exists()):
    tempdb = dbman.get_db()
    # check if tempdb was created today, if not purge the data and start fresh.
    print(f"db creation date: {tempdb['db_creation_date']}")
    logging.debug(f"db creation date: {tempdb['db_creation_date']}")
    if tempdb['db_creation_date'] != pretty_date:
        print(f"db was not created today, must have old data. Will be recreated!")
        logging.info(f"db was not created today, must have old data. Will be recreated!")
        tempdb = dbman.create_blank_db()
        dbman.write_database_to_disk(tempdb)
else:
    print("No database found, creating!")
    logging.debug("No database found, creating!")
    tempdb = dbman.create_blank_db()
    dbman.write_database_to_disk(tempdb)

# Check if db temperatures need to be updated, if so update them.
if indoor_temp > tempdb['indoor_max_temp']:
    print('Indoor temp is higher than temp in db. updating record.')
    logging.info('Indoor temp is higher than temp in db. updating record.')
    tempdb['indoor_max_temp'] = indoor_temp
    dbman.write_database_to_disk(tempdb)
    tempdb = dbman.get_db()
if outdoor_temp > tempdb['outdoor_max_temp']:
    print('Outdoor temp is higher than temp in db. updating record.')
    logging.info('Outdoor temp is higher than temp in db. updating record.')
    tempdb['outdoor_max_temp'] = outdoor_temp
    dbman.write_database_to_disk(tempdb)
    tempdb = dbman.get_db()

# Get the inside to outside temperature difference. Used for temp algo below.
daily_delta = tempdb['outdoor_max_temp'] - tempdb['indoor_max_temp']

if boundary == "close":
    get_notification_lock_status(tempdb)
    if (outdoor_temp - OUTSIDE_DEGREE_BUFFER) >= indoor_temp:
        # close windows
        print(f"CLOSE WINDOWS! {message}")
        push.send(TOKEN, USER, f"CLOSE WINDOWS! {message}")
        print("Sent Close windows notification")
        logging.debug(f"Updating notification status in DB.")
        tempdb['notification_sent'] = True
        dbman.write_database_to_disk(tempdb)
    else:
        # log temp and do nothing
        print(message)
        print("It's colder outside, recommend doing nothing!")
        logging.info(message)
        logging.info("It's colder outside, recommend doing nothing!")

if boundary == "open":
    get_notification_lock_status(tempdb)
    # If outside daytime high temp is $delta degrees higher than inside daytime high temp and
    # outside daytime high is above $trigger_temp
    print(f"daily temp delta: {daily_delta} DEGREE_DELTA setpoint: {DEGREE_DELTA} outdoor_max: {tempdb['outdoor_max_temp']} out_deg_trig: {OUTSIDE_DEGREE_TRIGGER}")
    logging.debug(f"daily temp delta: {daily_delta} DEGREE_DELTA setpoint: {DEGREE_DELTA} outdoor_max: {tempdb['outdoor_max_temp']} out_deg_trig: {OUTSIDE_DEGREE_TRIGGER}")
    if daily_delta >= DEGREE_DELTA and tempdb['outdoor_max_temp'] >= OUTSIDE_DEGREE_TRIGGER:
        # check to see if it's cooled off outside
        if (outdoor_temp - OUTSIDE_DEGREE_BUFFER) <= indoor_temp:
            print(message)
            push.send(TOKEN, USER, f"OPEN WINDOWS {message}")
            print("Sent OPEN windows notification")
            logging.debug(f"Updating Notification Status in DB - date: {date.strftime('%b %d, %Y')} status: {boundary}")
            tempdb['notification_sent'] = True
            dbman.write_database_to_disk(tempdb)
        # Nope still hot outside
        else:
            # log temp and do nothing
            print(message)
            print("It's WARMER outside, recommend doing nothing!")
            logging.info(message)
            logging.info("It's WARMER outside, recommend doing nothing!")
    else:
        print("It was not hot enough outside yet to trigger the window opening procedural calls. Recommend doing nothing!")
        logging.info("It was not hot enough outside yet to trigger the window opening procedural calls. Recommend doing nothing!")

if boundary == "OOB":
    print("Not in operational boundary.")
    logging.info(f"OOB: {message}")
