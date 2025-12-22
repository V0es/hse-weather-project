import pandas as pd
import plotly.graph_objects as go
import streamlit as st


@st.cache_data
def load_data(uploaded_file) -> pd.DataFrame | None:
    if uploaded_file is None:
        st.info("Пожалуйста, загрузите файл для продолжения.")
        return None
    return pd.read_csv(uploaded_file)


def plot_temperature_trends(data):
    df = data.copy()
    df["MA30"] = df["temperature"].rolling(window=30).mean()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["temperature"],
            mode="lines",
            name="Ежедневная температура",
            # legend=dict(title="Температура"),
            line=dict(color="black", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["MA30"],
            mode="lines",
            name="30-дневное скользящее среднее",
            # legend=dict(title="Скользящее среднее"),
            line=dict(color="orange", width=3),
        )
    )

    fig.update_layout(
        title="Температурные тренды с 30-дневным скользящим средним",
        xaxis_title="Дата",
        yaxis_title="Температура (°C)",
    )
    st.plotly_chart(fig, width="stretch")


st.set_page_config(page_title="Weather Analysis", page_icon=":cloud:", layout="wide")
st.title("Анализ температурных данных")

st.subheader("Загрузка исторических данных")

uploaded_file = st.file_uploader(
    "Выберите CSV файл с историческими температурными данными", type=["csv"]
)
data = load_data(uploaded_file)
if data is None:
    st.stop()
st.subheader("Предварительный просмотр данных")
st.table(data.head())
cities = data.city.unique()
selected_city = st.selectbox("Выберите город для анализа", cities)
city_data = data[data.city == selected_city]
plot_temperature_trends(city_data)
