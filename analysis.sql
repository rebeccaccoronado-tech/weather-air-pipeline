SELECT city, 
    ROUND(AVG(aqi_avg), 1) AS avg_aqi,
    MAX(aqi_max)           AS worst_aqi
FROM daily_air
GROUP BY city
ORDER BY avg_aqi DESC;

SELECT city, aqi_category, COUNT(*) AS days
FROM daily_air
GROUP BY city, aqi_category
ORDER BY city, days DESC;

SELECT a.date, a.city, a.aqi_max, w.temp_max_f, w.wind_max_mph
FROM daily_air AS a
JOIN daily_weather AS w
    ON w.city = a.city AND w.date = a.date
ORDER BY a.aqi_max DESC
LIMIT 10;

SELECT CASE
            WHEN w.temp_max_f >= 85 THEN 'Hot (85 and up)'
            WHEN w.temp_max_f >= 60 THEN 'Mild (60 to 84)'
            ELSE 'Cool (under 60)'
        END                       AS temp_band,
        COUNT(*)                  AS days,
        ROUND(AVG(a.aqi_avg), 1)  AS avg_aqi
FROM daily_weather AS w
JOIN daily_air AS a
    ON a.city = w.city AND a.date = w.date
GROUP BY temp_band
ORDER BY avg_aqi DESC;