from dataclasses import dataclass

BASE_GEO_URL = (
    "http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=5&appid={API_KEY}"
)


@dataclass
class Coordinates:
    lat: float
    lon: float


def get_city_coords(api_key: str, city_name: str) -> Coordinates: ...
