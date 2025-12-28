from dataclasses import dataclass

from aiohttp import ClientSession

from config import GEO_URL, WEATHER_URL


@dataclass
class Coordinates:
    lat: float
    lon: float


async def get_city_coords(
    session: ClientSession, city_name: str, api_key: str
) -> Coordinates:
    """Возвращает структуру координат для города по его названию

    Args:
        session (ClientSession): Объект сессии
        city_name (str): Название города
        api_key (str): Ключ OWM API

    Returns:
        Coordinates: Координаты города
    """
    async with session.get(
        url=GEO_URL.format(city=city_name, api_key=api_key)
    ) as response:
        resp_json = await response.json()
        city = resp_json[0]
        return Coordinates(city.get("lat"), city.get("lon"))


async def get_current_temperature(
    session: ClientSession, coords: Coordinates, api_key: str
) -> float:
    """Возвращает текущую температуру в градусах Цельсия по переданным координатам

    Args:
        session (ClientSession): Объект сессии
        coords (Coordinates): Координаты
        api_key (str): Ключ OWM API

    Returns:
        float: Текущая температура
    """
    async with session.get(
        WEATHER_URL.format(
            lat=coords.lat,
            lon=coords.lon,
            part="minutely,hourly,daily,alerts",
            api_key=api_key,
            units="metric",
        )
    ) as response:
        resp_json = await response.json()
        return resp_json.get("main").get("temp")
