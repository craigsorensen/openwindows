# Get weather from openweathermap api
  
# import required modules 
import requests
import json 
import logging

class WeatherMan:
    '''
    WeatherMan takes a API key and zipcode and returns the weather for that location.
    '''

    def __init__(self, key, zipcode):
        self.key = key
        self.zipcode = zipcode
        self.weather = self._get_weather

    @property
    def _get_weather(self):

        # base_url variable to store url 
        BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"

        # complete_url variable to store 

        complete_url = BASE_URL + "appid=" + self.key + "&q=" + self.zipcode + "&units=imperial"
        logging.debug(f"Weather URL: {complete_url}")
        response = requests.get(complete_url) 
        r = response.json() 
        logging.debug(f"Weather API response: {r}")

        if r["cod"] == 200: 
            
            m = r["main"] 
            current_temperature = m["temp"] 
            current_humidiy = m["humidity"]     
            w = r["weather"]

            # print(f"Temperature: {str(current_temperature)}F") 
            # print(f"Humidity: {str(current_humidiy)}%") 
        elif r["cod"] == 404:
            print(f"City Not Found for: {zipcode}")
            logging.info(f"City Not Found for: {zipcode}")
        else:
            print(f"Error {r['cod']} - {r['message']}")
            logging.info(f"Error {r['cod']} - {r['message']}")
            exit()
        
        return { "tempurature": current_temperature, "humidity": current_humidiy }

    @property
    def temperature(self):
        # print(f"Temperature: {self.weather['tempurature']} \N{DEGREE SIGN}F")
        return self.weather['tempurature']
    
    @property
    def humidity(self):
        # print(f"Humidity: {self.weather['humidity']}%")
        return self.weather['humidity']
