import asyncio
from datetime import datetime

import modin.pandas as mpd
import pandas as pd
import plotly.express as px
import streamlit as st
from aiohttp import ClientResponseError, ClientSession

from analysis import get_season_thresholds, get_year_stats, process_city
from config import COLUMN_NAMES, MONTH_TO_SEASON, SEASON_COLORS, SEASON_NAMES
from owm import get_city_coords, get_current_temperature
from plots import get_figure, get_plot
from utils import async_timeit, sync_timeit


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
    cities_df = df.groupby("city").apply(process_city)
    for city in cities:
        city_df = cities_df[cities_df["city"] == city]  # type: ignore
        cities_data[city] = pd.DataFrame(city_df, columns=city_df.columns)

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
    cities_df = data.groupby("city").apply(process_city)
    for city in cities:
        city_df = cities_df[cities_df["city"] == city]  # type: ignore
        cities_data[city] = city_df

    return cities_data


def load_data(uploaded_file) -> pd.DataFrame:
    """Преобразует загруженный файл в DataFrame

    Args:
        uploaded_file: Загруженный файл

    Returns:
        pd.DataFrame: Созданный DataFrame
    """

    return pd.read_csv(uploaded_file, parse_dates=["timestamp"])


def main():
    st.set_page_config(
        page_title="Weather Analysis", page_icon=":cloud:", layout="wide"
    )
    st.title("Анализ температурных данных")
    st.subheader("Загрузка исторических данных")
    uploaded_file = st.file_uploader(
        "Выберите CSV файл с историческими температурными данными", type=["csv"]
    )
    if uploaded_file is None:
        st.info("Пожалуйста, загрузите файл для продолжения.")
        st.stop()

    data = load_data(uploaded_file)
    data["season"] = data["season"].map(SEASON_NAMES)
    cities = data.city.unique()

    st.subheader("Анализ данных")

    if "cities_data" not in st.session_state:
        _, seq_time = get_cities_data_sequential(cities, data)
        cities_data, par_time = get_cities_data_parallel(cities, data)
        st.session_state.cities_data = cities_data
        st.session_state.seq_time = seq_time
        st.session_state.par_time = par_time

    else:
        cities_data = st.session_state.cities_data

    st.write(f"Последовательная обработка заняла {st.session_state.seq_time} секунд")
    st.write(f"Параллельная обработка заняла {st.session_state.par_time} секунд")

    selected_city = st.selectbox("Выберите город для анализа", cities)
    processed_data = cities_data[selected_city]

    st.subheader("Просмотр данных")
    st.dataframe(
        data[data.city == selected_city].reset_index(drop=True), width="content"
    )

    stats_df = get_year_stats(processed_data)

    st.subheader("Описательная статистика")
    st.dataframe(stats_df.rename(columns=COLUMN_NAMES))

    global_max = processed_data.loc[processed_data["temperature"].argmax()]
    global_min = processed_data.loc[processed_data["temperature"].argmin()]

    st.markdown(
        f"Максимальная температура за 9 лет: **{global_max.temperature:.3f} °C** была в **{global_max.year}** году"
    )
    st.markdown(
        f"Минимальная температура за 9 лет: **{global_min.temperature:.3f} °C** была в **{global_min.year}** году"
    )

    st.subheader("Визуализация")

    temperature_plot = get_plot(
        x=processed_data.timestamp,
        y=processed_data.temperature,
        mode="lines",
        name="Температура по дням, °C",
    )
    ma30_plot = get_plot(
        x=processed_data.timestamp,
        y=processed_data.ma30,
        mode="lines",
        name="Скользящее среднее с окном 30 дней",
        line_color="orange",
        line_width=3,
    )

    temp_fig = get_figure(
        [temperature_plot, ma30_plot],
        title="Общий график температуры",
        xlabel="Дата",
        ylabel="Температура, °C",
    )

    st.plotly_chart(temp_fig)
    season_fig = px.line(
        processed_data,
        "timestamp",
        "temperature",
        color="season",
        line_group="season_code",
        color_discrete_map=SEASON_COLORS,
        title="График по сезонам с выделением аномалий",
    )

    upper_bound_fig = px.line(
        processed_data, "timestamp", "upper", line_group="season_code"
    )
    upper_bound_fig.update_traces(line=dict(color="purple", dash="dash"))
    lower_bound_fig = px.line(
        processed_data, "timestamp", "lower", line_group="season_code"
    )
    lower_bound_fig.update_traces(line=dict(color="purple", dash="dash"))

    anomalies = processed_data[processed_data["is_anomaly"]]

    season_fig.add_scatter(
        x=anomalies.timestamp,
        y=anomalies.temperature,
        mode="markers",
        name="Аномалия в данных",
        marker=dict(size=8, symbol="circle", color="black"),
    )
    season_fig.add_traces(upper_bound_fig.data)
    season_fig.add_traces(lower_bound_fig.data)

    season_fig.update_layout(dict(xaxis_title="Дата", yaxis_title="Температура, °C"))

    st.plotly_chart(season_fig)

    st.subheader("Текущая температура")

    owm_api_key = st.text_input(
        "Введите ключ для OpenWeatherMap API", placeholder="Ваш ключ..."
    )
    if not owm_api_key:
        st.stop()

    if "temperatures" not in st.session_state:
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

    current_temperature = temperatures[selected_city]
    st.write(f"Синхронные запросы к API заняли {st.session_state.sync_time} секунд")
    st.write(f"Асинхронные запросы к API заняли {st.session_state.async_time} секунд")

    st.info(
        f"Текущая температура в городе **{selected_city}**: {current_temperature} °С"
    )

    current_season = MONTH_TO_SEASON[datetime.now().month]
    lower, upper = get_season_thresholds(processed_data, current_season)

    if lower <= current_temperature <= upper:
        st.success(
            f"Данная температура является **нормальной** для сезона **{current_season.lower()}** в городе **{selected_city}**"
        )
    elif current_temperature > upper:
        st.warning(
            f"Данная температура является **аномально** высокой для сезона **{current_season.lower()}** в городе **{selected_city}**."
            f"Нормальная температура: от {lower} до {upper}"
        )
    elif current_temperature < lower:
        st.warning(
            f"Данная температура является **аномально** низкой для сезона **{current_season.lower()}** в городе **{selected_city}**."
            f"Нормальная температура: от {lower} до {upper}"
        )


if __name__ == "__main__":
    main()
