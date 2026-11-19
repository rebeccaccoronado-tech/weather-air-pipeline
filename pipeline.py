# pipeline.py - pulls weather and air quality data, cleans it, and stores it.
import sqlite3

import pandas as pd
import requests

# --------Settings ----------
CITIES = {
    "Chicago": (41.88, -87.63),
    "Denver": (39.74, -104.99), 
    "Los Angeles": (34.05, -118.24),
    "St. Louis": (38.63, -90.20)
}
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
PAST_DAYS = 92

# ----------- Extract -----------
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
# ------------Transform ---------
def clean(df):
    rows_before = len(df)
    df["time"] = pd.to_datetime(df["time"])
    df["date"] = df["time"].dt.date.astype(str)
    df = df.drop_duplicates(subset=["city", "time"])
    df = df.dropna()
    newest_date = df.groupby("city")["date"]. transform("max")
    df = df[df["date"] < newest_date]
    print(" kept", len(df), "of", rows_before, "hourly rows")
    return df

def aqi_category(aqi) :
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    if aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    if aqi <= 200:
        return "Unhealthy"
    if aqi <=300:
        return "Very Unhealthy"
    return "Hazardous"

def transform(weather, air):
    weather = clean(weather)
    weather = weather[weather["temperature_2m"].between(-80, 135)]
    daily_weather = weather.groupby(["city", "date"]).agg(
        temp_avg_f=("temperature_2m", "mean"),
        temp_max_f=("temperature_2m", "max"), 
        temp_min_f=("temperature_2m", "min"),
        precip_in=("precipitation", "sum"), 
        wind_max_mph=("wind_speed_10m", "max"), 
    ).round(1).reset_index()

    air = clean(air)
    daily_air = air.groupby(["city", "date"]).agg(
        aqi_avg=("us_aqi", "mean"), 
        aqi_max=("us_aqi", "max"), 
        pm25_avg=("pm2_5", "mean"), 
    ).round(1).reset_index()
    daily_air["aqi_category"] = daily_air["aqi_max"].apply(aqi_category)
    return daily_weather, daily_air
#----------- Load ----------
SUMMARY_QUERY = """
SELECT w.date, w.city, 
    w.temp_avg_f, w.temp_max_f, w.temp_min_f, w.precip_in, w.wind_max_mph,
    a.aqi_avg, a.aqi_max, a.pm25_avg, a.aqi_category
FROM daily_weather AS w
JOIN daily_air AS a
    ON a.city = w.city AND a.date = w.date
ORDER BY w.date, w.city
"""

def load(daily_weather, daily_air) :
    conn = sqlite3.connect("data/weather.db")
    daily_weather.to_sql("daily_weather", conn, if_exists="replace", index=False)
    daily_air.to_sql("daily_air", conn, if_exists="replace", index=False)
    summary = pd.read_sql(SUMMARY_QUERY, conn)
    summary.to_csv("data/daily_summary.csv", index=False)
    conn.close()
    print("Loaded", len(summary), "daily rows")
# ----------- Run ----------
weather, air = extract()
daily_weather, daily_air = transform(weather, air)
load(daily_weather, daily_air)
print("Done.")