# Get weather from weatherapi.com
  
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
        BASE_URL = "http://api.weatherapi.com/v1/current.json?"

        # complete_url variable to store 
        complete_url = f'{BASE_URL}key={self.key}&q={self.zipcode}&aqi=no'
        logging.debug(f"Weather URL: {complete_url}")
        #print(f'URI: {complete_url}')
        response = requests.get(complete_url) 
        r = response.json() 
        logging.debug(f"Weather API response: {r}")
        #print(f"Weather API response: {r}")

        if response.status_code == 200: 
            
            c = r["current"] 
            current_temperature = c["temp_f"] 
            current_humidiy = c["humidity"]     

            #print(f"Temperature: {str(current_temperature)}F") 
            #print(f"Humidity: {str(current_humidiy)}%") 
        elif response.status_code == 404:
            print(f"City Not Found for: {zipcode}")
            logging.info(f"City Not Found for: {zipcode}")
        else:
            print(f"Error {response.status_code}")
            logging.info(f"Error {response.status_code}")
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
