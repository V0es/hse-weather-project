import modin.pandas as mpd
import pandas as pd


def get_moving_average(temperature: pd.Series, window: int = 30) -> pd.Series:
    """
    Возвращает скользящее среднее для ряда с выбранным окном

    Args:
        temperature (pd.Series): Ряд температур
        window (int, optional): Окно скользящего среднего. По умолчанию 30.

    Returns:
        pd.Series: Скользящее среднее
    """
    return temperature.rolling(window=window).mean()


def process_city(city_df: pd.DataFrame) -> pd.DataFrame:
    """
    Обработка датафрейма для конкретного города.
    Выделение года, добавление скользящего среднего, кодировка сезона для корректного подсчёта среднего и
    стандартного отклонения по сезонам, определение границ mean +- 2 * std, отметка аномалий.


    Args:
        city_df (pd.DataFrame): Датафрейм с данными о температуре для конкретного города

    Returns:
        pd.DataFrame: Датафрейм с обработанными данными
    """
    df = city_df.copy()
    df["year"] = df["timestamp"].dt.year  # type: ignore
    df["ma30"] = get_moving_average(df.temperature)

    # кодировка сезона в связи с переходом года для зимы
    df["season_code"] = (df.season != df.season.shift()).cumsum()

    season_stats = df.groupby("season_code")["temperature"].agg(["mean", "std"])

    res_df = df.merge(season_stats, on=["season_code"], how="left")

    res_df["upper"] = res_df["mean"] + 2 * res_df["std"]
    res_df["lower"] = res_df["mean"] - 2 * res_df["std"]
    res_df["is_anomaly"] = (res_df.temperature > res_df["upper"]) | (
        res_df.temperature < res_df["lower"]
    )
    return res_df


def get_year_stats(data: pd.DataFrame | mpd.DataFrame) -> pd.DataFrame:
    """
    Общие статистики для температура по годам и сезонам

    Args:
        data (pd.DataFrame): Исходный датафрейм с температурой

    Returns:
        pd.DataFrame: Датафрейм с обработанными данными
    """
    df = data.copy()
    stats = (
        df.groupby(["year", "season"])
        .agg(
            mean_temp=("temperature", "mean"),
            min_temp=("temperature", "min"),
            max_temp=("temperature", "max"),
            std_temp=("temperature", "std"),
            anomaly_count=("is_anomaly", "sum"),
        )
        .reset_index()
    )

    return stats


def get_season_thresholds(city_df: pd.DataFrame, season: str) -> tuple[float, float]:
    """
    Вычисление нижнего и верхнего порогов аномалий для конкретного сезона

    Args:
        city_df (pd.DataFrame): Датафрейм с данными о температуре для конкретного города
        season (str): Название сезона

    Returns:
        tuple[float, float]: Кортеж из нижнего и верхнего порогов аномалий
    """
    df = city_df.copy()
    overall_season_stats = (
        df.groupby("season")["temperature"].agg(["mean", "std"]).reset_index()
    )

    lower = (
        overall_season_stats[overall_season_stats["season"] == season]["mean"].item()
        - 2
        * overall_season_stats[overall_season_stats["season"] == season]["std"].item()
    )
    upper = (
        overall_season_stats[overall_season_stats["season"] == season]["mean"].item()
        + 2
        * overall_season_stats[overall_season_stats["season"] == season]["std"].item()
    )

    return lower, upper
