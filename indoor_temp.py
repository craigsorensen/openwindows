import adafruit_dht
import time
import board

# --------- User Settings ---------
SENSOR_LOCATION_NAME = "Office"
METRIC_UNITS = False
# ---------------------------------

dhtSensor = adafruit_dht.DHT22(board.D4)

def get_indoor_temperature():
    humidity = dhtSensor.humidity
    temp_c = dhtSensor.temperature
    if METRIC_UNITS:
            print(f"{SENSOR_LOCATION_NAME} Temperature(C), {temp_c}")
            temperature = temp_c
    else:
            temp_f = format(temp_c * 9.0 / 5.0 + 32.0, ".2f")
            print(f"{SENSOR_LOCATION_NAME} Temperature(F), {temp_f}")
            temperature = temp_f
    humidity = format(humidity,".2f")
    print(f"{SENSOR_LOCATION_NAME} Humidity(%), {humidity}")
    return {"temperature": temperature, "humidity": humidity}
