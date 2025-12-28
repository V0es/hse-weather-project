GEO_URL = (
    "http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=5&appid={api_key}"
)

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&exclude={part}&appid={api_key}&units={units}"


SEASON_COLORS = {
    "Зима": "blue",
    "Весна": "green",
    "Лето": "red",
    "Осень": "orange",
}

SEASON_NAMES = {
    "winter": "Зима",
    "spring": "Весна",
    "summer": "Лето",
    "autumn": "Осень",
}

COLUMN_NAMES = {
    "year": "Год",
    "season": "Сезон",
    "mean_temp": "Средняя температура, °C",
    "min_temp": "Минимальная температура, °C",
    "max_temp": "Максимальная температура, °C",
    "anomaly_count": "Число аномалий",
    "std_temp": "Стандартное отклонение",
    "city": "Город",
    "timestamp": "Дата",
    "temperature": "Температура, °C",
}

MONTH_TO_SEASON = {
    12: "Зима",
    1: "Зима",
    2: "Зима",
    3: "Весна",
    4: "Весна",
    5: "Весна",
    6: "Лето",
    7: "Лето",
    8: "Лето",
    9: "Осень",
    10: "Осень",
    11: "Осень",
}
