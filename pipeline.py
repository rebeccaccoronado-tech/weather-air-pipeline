# pipeline.py - pulls weather and air quality data, cleans it, and stores it.
import sqlite3

import pandas as pd
import requests

# --------Settings ----------
CITIES = {
    "Chicago": (41.88, -87.63),
    "Devner": (39.74, -104.99), 
    "Los Angeles": (34.05, -118.24),
    "St. Louis": (38.63, -90.20)
}
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
PAST_DAYS = 92

# ----------- Step 1: Extract -----------
def fetch (url, params):
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return pd.DataFrame(response.json()["hourly"])
#get data and return table, data stored under name 'response'. Details chnge based on what is input and the attempt timesout after 30 seconds. 
#checks if the reply is an error. If so, the program stops. Turns the section into a table. Only an hourly response will be given. 

def extract ():
    weather_list = []
    air_list = []
    for city, (lat, lon) in CITIES.items():
        print ("Extracting", city)
        weather = fetch (WEATHER_URL, {
            "latitude" : lat, 
            "longitude": lon, 
            "hourly": "temperature_2m,precipitation,wind_speed_10m",
            "past_days": PAST_DAYS,
            "forecast_days": 1, 
            "timezone": "auto", 
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph", 
            "precipitation_unit": "inch",
        })
    #Makes empty lists to hold weather and air quality data. 'for' = loop. Gets same info for each city. 
    #Shows "extracting city_name" while processing.
    #Fetches data from the weather address
    #number_m is number of meters above ground
    #forecast includes today and a total of 92 days.
        air = fetch(AIR_URL, {
            "latitude": lat, 
            "longitude": lon,
            "hourly": "us_aqi,pm2_5", 
            "past_days": PAST_DAYS,
            "forecast_days": 1,
            "timezone": "auto", 
        })
#pm2_5 is fine particle pollution
        weather["city"] = city
        air["city"] = city
        weather_list.append(weather)
        air_list.append(air)
#Adds a city column to the weather/air tables and fills it with the city's name. Adds city's weather and air tables to the list 'at the end'.
    weather = pd.concat(weather_list)
    air = pd.concat(air_list)
    weather.to_csv("data/raw_weather.csv", index=False)
    air.to_csv("data/raw_air.csv", index=False)
    return weather, air
#Stacks cities' tables into one tall table for both weather and air quality. Saves weather data as a file. Leaves out pandas' own row numbers ('false').
# ----------- Run ----------
weather, air = extract()
print(weather.head())