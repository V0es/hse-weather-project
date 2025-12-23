from typing import Iterable

import pandas as pd
import plotly.graph_objects as go


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
