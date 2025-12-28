import asyncio

import streamlit as st
from aiohttp import ClientResponseError, ClientSession

from owm import get_city_coords, get_current_temperature
from utils import async_timeit


@async_timeit
async def get_temperatures_sync(cities: list[str], api_key: str) -> dict[str, float]:
    """
    Синхронно by design собирает текущую температуру для списка городов и возвращает словарь
    Применён декоратор для измерения времени выполнения
    Args:
        cities (list[str]): Список городов
        api_key (str): Ключ API OWM

    Returns:
        dict[str, float]: Словарь город: температура
    """
    result = {}
    async with ClientSession(raise_for_status=True) as session:
        for city in cities:
            city_coords = await get_city_coords(session, city, api_key)
            result[city] = await get_current_temperature(session, city_coords, api_key)
    return result


@async_timeit
async def get_temperatures_async(cities: list[str], api_key: str) -> dict[str, float]:
    """
    Асинхронно собирает текущую температуру для списка городов и возвращает словарь
    Применён декоратор для измерения времени выполнения
    Args:
        cities (list[str]): Список городов
        api_key (str): Ключ API OWM

    Returns:
        dict[str, float]: Словарь город: температура
    """
    async with ClientSession(raise_for_status=True) as session:
        coord_tasks = [get_city_coords(session, city, api_key) for city in cities]
        coords = await asyncio.gather(*coord_tasks)

        temperature_tasks = [
            get_current_temperature(session, coord, api_key) for coord in coords
        ]
        temperatures = await asyncio.gather(*temperature_tasks)

        result = {city: temp for city, temp in zip(cities, temperatures)}

    return result


def get_temperatures_table(cities: list[str], owm_api_key: str) -> dict[str, float]:
    """
    Получает таблицу текущих температур для списка городов
    Сравнивает время выполнения синхронного и асинхронного сбора данных

    Args:
        cities (list[str]): Список городов
        owm_api_key (str): API ключ OWM

    Returns:
        dict[str, float]: Словарь текущих температур для городов
    """
    if "temperatures" not in st.session_state:
        # Здесь происходит сравнение времени выполнения синхронного и асинхронного сбора данных
        # Асинхронный сбор данных выигрывает за счёт переключения контекста во время ожидания ответов от API
        try:
            _, sync_time = asyncio.run(get_temperatures_sync(cities, owm_api_key))
            temperatures, async_time = asyncio.run(
                get_temperatures_async(cities, owm_api_key)
            )
            st.session_state.temperatures = temperatures
            st.session_state.sync_time = sync_time
            st.session_state.async_time = async_time
        except ClientResponseError as exc:
            st.error(exc)
            st.stop()
    else:
        temperatures = st.session_state.temperatures
    return temperatures
