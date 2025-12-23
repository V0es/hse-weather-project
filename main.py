import pandas as pd
import streamlit as st

from plots import get_figure, get_plot

SEASON_COLORS = {
    "winter": "blue",
    "spring": "green",
    "summer": "red",
    "autumn": "orange",
}


@st.cache_data
def load_data(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        st.info("Пожалуйста, загрузите файл для продолжения.")
        st.stop()
    return pd.read_csv(uploaded_file)


def plot_temperature_trends(data: pd.DataFrame):
    df = data.copy()

    ma30 = df.temperature.rolling(window=30).mean().shift()

    temp_plot = get_plot(
        x=df.timestamp, y=df.temperature, mode="lines", name="Температура по дням"
    )
    ma30_plot = get_plot(
        x=df.timestamp,
        y=ma30,
        mode="lines",
        name="Скользящее среднее с 30-дневным окном",
        line_color="orange",
        line_width=3,
    )

    temp_figure = get_figure(
        [temp_plot, ma30_plot],
        title="График температуры с 30-дневным скользящим средним",
        xlabel="Дата",
        ylabel="Температура (°C)",
    )

    st.plotly_chart(temp_figure, width="stretch")


def plot_seasons(data: pd.DataFrame):
    df = data.copy()

    df["season_block"] = (df["season"] != df["season"].shift()).cumsum()
    stats = df.groupby("season_block")["temperature"].agg(["mean", "std"])

    plots = []

    for block_id, block in df.groupby("season_block"):
        season = block["season"].iloc[0]
        mean = stats.loc[block_id, "mean"]
        std = stats.loc[block_id, "std"]

        upper = mean + 2 * std
        lower = mean - 2 * std

        plots.append(
            get_plot(
                x=block["timestamp"],
                y=block["temperature"],
                mode="lines",
                line_color=SEASON_COLORS[season],
                line_width=2,
                name=season,
                showlegend=False,
            )
        )

        for offset in [2 * std, -2 * std]:
            plots.append(
                get_plot(
                    x=[block["timestamp"].min(), block["timestamp"].max()],
                    y=[mean + offset] * 2,
                    mode="lines",
                    line_color="purple",
                    line_width=1,
                    line_dash="dash",
                    showlegend=False,
                )
            )

        outliers = block[
            (block["temperature"] > upper) | (block["temperature"] < lower)
        ]
        if not outliers.empty:
            plots.append(
                get_plot(
                    x=outliers["timestamp"],
                    y=outliers["temperature"],
                    mode="markers",
                    marker_color=SEASON_COLORS[season],
                    marker_size=8,
                    name=f"{season} выбросы",
                    showlegend=False,
                )
            )
    for season, color in SEASON_COLORS.items():
        plots.append(
            get_plot(
                x=[None],
                y=[None],
                mode="lines",
                line_color=color,
                line_width=2,
                name=season,
            )
        )
    plots.append(
        get_plot(
            x=[None],
            y=[None],
            mode="lines",
            line_color="purple",
            name=r"$\mu  2 \cdot \sigma$",
        )
    )

    figure = get_figure(
        plots, title="Сезонные аномалии", xlabel="Дата", ylabel="Температура (°C)"
    )

    st.plotly_chart(figure)


st.set_page_config(page_title="Weather Analysis", page_icon=":cloud:", layout="wide")
st.title("Анализ температурных данных")

st.subheader("Загрузка исторических данных")

uploaded_file = st.file_uploader(
    "Выберите CSV файл с историческими температурными данными", type=["csv"]
)
data = load_data(uploaded_file)
data.timestamp = pd.to_datetime(data.timestamp)
st.subheader("Предварительный просмотр данных")
st.table(data.head())
cities = data.city.unique()
selected_city = st.selectbox("Выберите город для анализа", cities)
city_data = data[data.city == selected_city]
plot_temperature_trends(city_data)
plot_seasons(city_data)
