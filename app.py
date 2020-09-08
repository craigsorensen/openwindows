import adafruit_dht
import time
import board

# --------- User Settings ---------
SENSOR_LOCATION_NAME = "Office"
BUCKET_NAME = ":partly_sunny: Room Temperatures"
BUCKET_KEY = "dht22sensor"
ACCESS_KEY = "ENTER ACCESS KEY HERE"
MINUTES_BETWEEN_READS = 10
METRIC_UNITS = False
# ---------------------------------

dhtSensor = adafruit_dht.DHT22(board.D4)

while True:
        humidity = dhtSensor.humidity
        temp_c = dhtSensor.temperature
        if METRIC_UNITS:
                print(f"{SENSOR_LOCATION_NAME} Temperature(C), {temp_c}")
        else:
                temp_f = format(temp_c * 9.0 / 5.0 + 32.0, ".2f")
                print(f"{SENSOR_LOCATION_NAME} Temperature(F), {temp_f}")
        humidity = format(humidity,".2f")
        print(f"{SENSOR_LOCATION_NAME} Humidity(%), {humidity}")
        time.sleep(60*MINUTES_BETWEEN_READS)
