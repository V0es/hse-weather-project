import pandas as pd
import plotly.express as px
import streamlit as st

from analysis import get_year_stats, process_city
from plots import get_figure, get_plot

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


@st.cache_data
def load_data(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        st.info("Пожалуйста, загрузите файл для продолжения.")
        st.stop()
    return pd.read_csv(uploaded_file, parse_dates=["timestamp"])


st.set_page_config(page_title="Weather Analysis", page_icon=":cloud:", layout="wide")
st.title("Анализ температурных данных")

st.subheader("Загрузка исторических данных")

uploaded_file = st.file_uploader(
    "Выберите CSV файл с историческими температурными данными", type=["csv"]
)
data = load_data(uploaded_file)
data["season"] = data["season"].map(SEASON_NAMES)
cities = data.city.unique()

st.subheader("Анализ данных")

selected_city = st.selectbox("Выберите город для анализа", cities)
city_data = data[data.city == selected_city]

st.subheader("Просмотр данных")
st.dataframe(city_data.reset_index(drop=True))


processed_data = process_city(city_data)

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


upper_fig = px.line(processed_data, "timestamp", "upper", line_group="season_code")
upper_fig.update_traces(line=dict(color="purple", dash="dash"))
lower_fig = px.line(processed_data, "timestamp", "lower", line_group="season_code")
lower_fig.update_traces(line=dict(color="purple", dash="dash"))

anomalies = processed_data[processed_data["is_anomaly"]]

season_fig.add_scatter(
    x=anomalies.timestamp,
    y=anomalies.temperature,
    mode="markers",
    name="Аномалия в данных",
    marker=dict(size=8, symbol="circle", color="black"),
)
season_fig.add_traces(upper_fig.data)
season_fig.add_traces(lower_fig.data)

season_fig.update_layout(dict(xaxis_title="Дата", yaxis_title="Температура, °C"))


st.plotly_chart(season_fig)


owm_api_key = st.text_input(
    "Введите ключ для OpenWeatherMap API", placeholder="Ваш ключ..."
)
if not owm_api_key:
    st.stop()
