import os
import logging
import indoor_temp.indoor_temp

from datetime import datetime
from weather_api import weather

CRED_DIR = os.path.expanduser("~")
api_key_file = "{0}/.openweatherapi.txt".format(CRED_DIR)
SCRIPT_EXC_DIR = os.path.dirname(os.path.realpath(__file__))
lock_file_location = "{0}/push.lock".format(SCRIPT_EXC_DIR)
log_dir = f'{SCRIPT_EXC_DIR}/app.log'
LOCAL_ZIPCODE = "97477"
date = datetime.now()

# Setup logging
logging.basicConfig(filename=log_dir, format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', level=logging.INFO)

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

# print(CRED_DIR)
# print(api_key_file)
# print(WEATHER_API_KEY)
# print(LOCAL_ZIPCODE)

indoor = int(indoor_temp()['tempurature'])
outdoor = int((weather.WeatherMan(WEATHER_API_KEY, LOCAL_ZIPCODE)).temperature)
hour = int(date.strftime("%H"))
morning = False
DEGREE_BUFFER = 2

if hour <= 11:
    morning = True


#outside = weather.WeatherMan(WEATHER_API_KEY, LOCAL_ZIPCODE)
#indoor =  indoor_temp()

if morning:
    if os.path.isfile(lock_file_location):
        with open(lock_file_location, 'r') as f:
            lock_file_contents = f.readlines()
            lock_file_contents = [e.strip() for e in lock_file_contents]
        if lock_file_contents[0] == date.strftime("%b %d, %Y"):
            print("Found lockfile. Has notification already been sent?")
            logging.info("Found lockfile. Has notification already been sent today?")
            logging.info(f"Lockfile Location: {lock_file_location}")
            logging.info(f"Lockdate: {lock_file_contents}")
            quit()
        else:
            print("Old lockfile found, removing!")
            logging.info("Old lockfile found, removing!")
            os.remove(lock_file_location)
    if (outdoor - DEGREE_BUFFER) >= indoor:
        # close windows
        print(f"Inside: {indoor} - Outside: {outdoor - DEGREE_BUFFER}")
        print("Sent Close windows notification")
        logging.debug(f"Writing lock file - date: {date.strftime('%b %d, %Y')} morning: {morning}")
    
        with open(lock_file_location, 'w') as f:
            f.write(date.strftime("%b %d, %Y")+"\n")
            f.write(f"{morning}\n")
    else:
        #log temp and do nothing
        print(f"Inside: {indoor} || Outside: {outdoor} || Outside Adjusted: {outdoor - DEGREE_BUFFER}")
        print("It's colder outside, recommend doing nothing!")

if not morning:
    if os.path.isfile(lock_file_location):
        with open(lock_file_location, 'r') as f:
            lock_file_contents = f.readlines()
            lock_file_contents = [e.strip() for e in lock_file_contents]
        if lock_file_contents[0] == date.strftime("%b %d, %Y") and bool(lock_file_contents[1]):
            print("Found lockfile. Has notification already been sent?")
            logging.info("Found lockfile. Has notification already been sent today?")
            logging.info(f"Lockfile Location: {lock_file_location}")
            logging.info(f"Lockdate: {lock_file_contents}")
            quit()
        else:
            print("Old lockfile found, removing!")
            logging.info("Old lockfile found, removing!")
            os.remove(lock_file_location)
    if (outdoor - DEGREE_BUFFER) <= indoor:
        print(f"Inside: {indoor} - Outside: {outdoor - DEGREE_BUFFER}")
        print("Sent OPEN windows notification")
        logging.debug(f"Writing lock file - date: {date.strftime('%b %d, %Y')} morning: {morning}")
    
        with open(lock_file_location, 'w') as f:
            f.write(date.strftime("%b %d, %Y")+"\n")
            f.write(f"{morning}\n")

    else:
        #log temp and do nothing
        print(f"Inside: {indoor} || Outside: {outdoor} || Outside Adjusted: {outdoor - DEGREE_BUFFER}")
        print("It's WARMER outside, recommend doing nothing!")