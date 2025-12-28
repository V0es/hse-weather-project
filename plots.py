from typing import Iterable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import SEASON_COLORS


def get_plot(
    x: pd.Series,
    y: pd.Series,
    mode: str,
    name: str | None = None,
    line_color: str = "black",
    line_width: int = 1,
    **kwargs,
) -> go.Scatter:
    plot = go.Scatter(
        x=x,
        y=y,
        mode=mode,
        name=name,
        line=dict(color=line_color, width=line_width),
        **kwargs,
    )

    return plot


def get_figure(
    plots: Iterable[go.Scatter], title: str, xlabel: str, ylabel: str
) -> go.Figure:
    figure = go.Figure()

    figure.add_traces(plots)

    figure.update_layout(
        title=title,
        xaxis_title=xlabel,
        yaxis_title=ylabel,
    )

    return figure


def get_common_temperature_figure(df: pd.DataFrame) -> go.Figure:
    temperature_plot = get_plot(
        x=df.timestamp,
        y=df.temperature,
        mode="lines",
        name="Температура по дням, °C",
    )
    ma30_plot = get_plot(
        x=df.timestamp,
        y=df.ma30,
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

    return temp_fig


def get_seasonal_temperature_figure(df: pd.DataFrame) -> go.Figure:
    season_fig = px.line(
        df,
        "timestamp",
        "temperature",
        color="season",
        line_group="season_code",
        color_discrete_map=SEASON_COLORS,
        title="График по сезонам с выделением аномалий",
    )

    upper_bound_fig = px.line(df, "timestamp", "upper", line_group="season_code")
    upper_bound_fig.update_traces(line=dict(color="purple", dash="dash"))
    lower_bound_fig = px.line(df, "timestamp", "lower", line_group="season_code")
    lower_bound_fig.update_traces(line=dict(color="purple", dash="dash"))

    anomalies = df[df["is_anomaly"]]

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

    return season_fig
