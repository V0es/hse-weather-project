from datetime import datetime

import pandas as pd
import streamlit as st

from analysis import (
    get_global_min_max,
    get_season_thresholds,
    get_year_stats,
)
from benchmark.cpubound import get_cities_data
from benchmark.iobound import get_temperatures_table
from config import COLUMN_NAMES, MONTH_TO_SEASON, SEASON_NAMES
from plots import (
    get_common_temperature_figure,
    get_seasonal_temperature_figure,
)


def load_data(uploaded_file) -> pd.DataFrame:
    """Преобразует загруженный файл в DataFrame

    Args:
        uploaded_file: Загруженный файл

    Returns:
        pd.DataFrame: Созданный DataFrame
    """

    return pd.read_csv(uploaded_file, parse_dates=["timestamp"])


def show_final_message(
    current_temperature: float,
    lower: float,
    upper: float,
    current_season: str,
    selected_city: str,
) -> None:
    """
    Показывает сообщение о том, является ли текущая температура аномальной или нормальной для текущего сезона в выбранном городе

    Args:
        current_temperature (float): Текущая температура
        lower (float): Нижняя граница нормальной температуры
        upper (float): Верхняя граница нормальной температуры
        current_season (str): Текущий сезон
        selected_city (str): Выбранный город
    """
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

    cities_data = get_cities_data(cities.tolist(), data)
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

    global_min, global_max = get_global_min_max(processed_data)

    st.markdown(
        f"Максимальная температура за 9 лет: **{global_max.temperature:.3f} °C** была в **{global_max.year}** году"
    )
    st.markdown(
        f"Минимальная температура за 9 лет: **{global_min.temperature:.3f} °C** была в **{global_min.year}** году"
    )

    st.subheader("Визуализация")

    common_temp_fig = get_common_temperature_figure(processed_data)
    st.plotly_chart(common_temp_fig)

    season_temp_fig = get_seasonal_temperature_figure(processed_data)
    st.plotly_chart(season_temp_fig)

    st.subheader("Текущая температура")
    owm_api_key = st.text_input(
        "Введите ключ для OpenWeatherMap API", placeholder="Ваш ключ..."
    )
    if not owm_api_key:
        st.stop()

    temperatures = get_temperatures_table(cities.tolist(), owm_api_key)

    current_temperature = temperatures[selected_city]
    st.write(f"Синхронные запросы к API заняли {st.session_state.sync_time} секунд")
    st.write(f"Асинхронные запросы к API заняли {st.session_state.async_time} секунд")

    st.info(
        f"Текущая температура в городе **{selected_city}**: {current_temperature} °С"
    )

    current_season = MONTH_TO_SEASON[datetime.now().month]
    lower, upper = get_season_thresholds(processed_data, current_season)

    show_final_message(
        current_temperature,
        lower,
        upper,
        current_season,
        selected_city,
    )


if __name__ == "__main__":
    main()
