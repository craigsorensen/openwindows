"""
Test script to pull outdoor temperature from Ambient Weather API.
Usage: python3 ambient_weather_test.py
"""

import requests
import json

# Replace these with your actual keys
API_KEY = "YOUR_API_KEY"
APP_KEY = "YOUR_APPLICATION_KEY"

url = "https://rt.ambientweather.net/v1/devices"
params = {
    "apiKey": API_KEY,
    "applicationKey": APP_KEY,
}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    last = data[0]["lastData"]

    print(f"Station: {data[0].get('info', {}).get('name', 'Unknown')}")
    print(f"Outdoor Temp: {last['tempf']} F")
    print(f"Indoor Temp:  {last['tempinf']} F")
    print(f"Humidity:     {last['humidity']}%")
    print(f"Last Updated: {last.get('date', 'unknown')}")
    print()
    print("Full lastData payload:")
    print(json.dumps(last, indent=2))
elif response.status_code == 401:
    print("Authentication failed -- check your API and Application keys.")
elif response.status_code == 429:
    print("Rate limited -- wait a moment and try again.")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
