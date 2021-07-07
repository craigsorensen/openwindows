import json
import os

from datetime import datetime

#variables
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
