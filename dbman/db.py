import json
import os

from datetime import datetime
# get temps
# check for max_temp_file, if not found, create.
# get previous max temps
# if current outside temp is higher than previous, update max_temp_file
# if current inside temp is higher than previous, update max_temp_file
# if outside temp is higher than highest inside temp + buffer, set send notification to true

#variables
indoor_temp = 71
outdoor_temp = 81
temp_buffer = 5


date = datetime.now() # get current date/time
pretty_date = date.strftime("%b-%d-%Y") #Nov-01-2021

class db_manager():
    def __init__(self, tempurature_db_location):
        #file locations
        self.db_location = tempurature_db_location
        self.date = datetime.now() # get current date/time
        self.pretty_date = self.date.strftime("%b-%d-%Y") #Nov-01-2021

    def create_blank_db(self):
        db = {}
        db["indoor_max_temp"] = 0
        db["outdoor_max_temp"] = 0
        db["db_creation_date"] = self.pretty_date
        db["send_notifcation"] = False
        db["notification_sent"] = False
        return db

    def get_db(self):
        with open(self.db_location, 'r') as f:
            db = json.load(f)
            return db

    def write_database_to_disk(self, data):
        with open(self.db_location, 'w') as f:
            json.dump(data, f)

    def check_if_db_file_exists(self):
        if os.path.isfile(self.db_location):
            print(f"db found in: {self.db_location}")
            return True
        # nope, return false.
        print(f"db not found in: {self.db_location}")
        return False

## Main ##

# print("Checking if tempdb exists..")
# if(dbman.check_if_db_file_exists()):
#     tempdb = dbman.get_db()
#     # check if tempdb was created today, if not purge the data and start fresh.
#     print(f"db creation date: {tempdb['db_creation_date']}")
# else:
#     print("No database found, creating!")
#     tempdb = dbman.create_blank_db()


# if tempdb['db_creation_date'] == pretty_date:
#     print("database was created today.. lets use it")
# else:
#     print("old database data found. Purge!")
#     tempdb = dbman.create_blank_db()
#     dbman.write_database_to_disk(tempdb)
#     print("loading new db from disk")
#     tempdb = dbman.get_db()



# Check if notification should be sent
# Current process is if outside temp is was ever 10 degrees warmer than inside.
