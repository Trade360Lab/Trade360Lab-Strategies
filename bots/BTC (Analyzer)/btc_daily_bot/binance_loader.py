def load_binance_klines(
    symbol: str = "BTCUSDT",
    interval: str = "5m",
    limit_total: int = 10_000,
) -> pd.DataFrame:
    """
    Тянем историю с Binance пачками по 1000 свечей, двигаясь назад во времени.
    Возвращает DataFrame с индексом datetime и колонками OHLCV.
    """
    url = "https://api.binance.com/api/v3/klines"
    all_klines = []
    end_time = None
    per_request = 1000

    while len(all_klines) < limit_total:
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": per_request,
        }

        if end_time is not None:
            params["endTime"] = end_time - 1

        session = requests.Session()
        session.trust_env = False  # не брать proxy из переменных окружения
        
        resp = session.get(url, params=params, timeout=20)
        resp.raise_for_status()
        klines = resp.json()

        if not klines:
            break

        all_klines = klines + all_klines
        end_time = klines[0][0]

        time.sleep(0.1)

    all_klines = all_klines[-limit_total:]

    df_binance = pd.DataFrame(all_klines, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "qav", "num_trades", "taker_base",
        "taker_quote", "ignore"
    ])

    numeric_cols = ["open", "high", "low", "close", "volume"]
    for col in numeric_cols:
        df_binance[col] = df_binance[col].astype(float)

    df_binance["datetime"] = pd.to_datetime(df_binance["open_time"], unit="ms", utc=True)

    df_binance = df_binance[["datetime", "open", "high", "low", "close", "volume"]]
    df_binance = df_binance.sort_values("datetime")
    df_binance = df_binance.drop_duplicates(subset=["datetime"])
    df_binance = df_binance.set_index("datetime")

    return df_binance