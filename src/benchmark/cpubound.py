import modin.pandas as mpd
import pandas as pd
import streamlit as st

from analysis import process_city
from utils import sync_timeit


@sync_timeit
def get_cities_data_parallel(
    cities: list[str], data: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """
    Обрабатывает данные по каждому городу параллельно и возвращает словарь

    Args:
        cities (list[str]): Список городов
        data (pd.DataFrame): Исходный датафрейм с температурой

    Returns:
        dict[str, pd.DataFrame]: Словарь город: обработанный датафрейм
    """
    cities_data = {}
    df = mpd.DataFrame(data)
    cities_df = df.groupby(("city",)).apply(process_city)
    for city in cities:
        city_df = cities_df[cities_df["city"] == city]  # type: ignore
        cities_data[city] = pd.DataFrame(city_df, columns=city_df.columns)  # type: ignore

    return cities_data


@sync_timeit
def get_cities_data_sequential(
    cities: list[str], data: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """
    Обрабатывает данные по каждому городу последовательно и возвращает словарь

    Args:
        cities (list[str]): Список городов
        data (pd.DataFrame): Исходный датафрейм с температурой

    Returns:
        dict[str, pd.DataFrame]: Словарь город: обработанный датафрейм
    """
    cities_data = {}
    cities_df = data.groupby(("city",)).apply(process_city)
    for city in cities:
        city_df = cities_df[cities_df["city"] == city]  # type: ignore
        cities_data[city] = city_df

    return cities_data


def get_cities_data(cities: list[str], data: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Получает обработанные данные по каждому городу
    Сравнивает время выполнения последовательной и параллельной обработки данных

    Args:
        cities (list[str]): Список городов
        data (pd.DataFrame): Исходный датафрейм с температурой
    Returns:
        dict[str, pd.DataFrame]: Словарь город: обработанный датафрейм
    """
    if "cities_data" not in st.session_state:
        # Здесь происходит сравнение времени выполнения последовательной и параллельной обработки данных
        # Последовательная обработка выигрывает за счёт меньших накладных расходов на управление распараллеливанием
        _, seq_time = get_cities_data_sequential(cities, data)
        cities_data, par_time = get_cities_data_parallel(cities, data)
        st.session_state.cities_data = cities_data
        st.session_state.seq_time = seq_time
        st.session_state.par_time = par_time

    else:
        cities_data = st.session_state.cities_data

    return cities_data
