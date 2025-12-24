import pandas as pd


def get_moving_average(temperature: pd.Series, window: int = 30) -> pd.Series:
    return temperature.rolling(window=window).mean()


def process_city(city_df: pd.DataFrame) -> pd.DataFrame:
    df = city_df.copy()
    df["year"] = df["timestamp"].dt.year
    df["ma30"] = get_moving_average(df.temperature)
    df["season_code"] = (df.season != df.season.shift()).cumsum()

    season_stats = df.groupby("season_code")["temperature"].agg(["mean", "std"])

    res_df = df.merge(season_stats, on=["season_code"], how="left")

    res_df["upper"] = res_df["mean"] + 2 * res_df["std"]
    res_df["lower"] = res_df["mean"] - 2 * res_df["std"]
    res_df["is_anomaly"] = (res_df.temperature > res_df["upper"]) | (
        res_df.temperature < res_df["lower"]
    )
    return res_df


def get_year_stats(data: pd.DataFrame) -> pd.DataFrame:
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
