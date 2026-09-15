import pandas as pd
import pytest

from scanner import download


def create_price_df(periods=300):
    dates = pd.date_range(
        "2025-01-01",
        periods=periods,
        freq="B",
    )
    return pd.DataFrame(
        {
            "Close": [100.0 + index for index in range(periods)],
            "High": [101.0 + index for index in range(periods)],
            "Low": [99.0 + index for index in range(periods)],
            "Volume": [1_000_000 + index for index in range(periods)],
        },
        index=dates,
    )


def test_safe_last_returns_latest_value():
    series = pd.Series([1.0, 2.0, 3.0])

    result = download.safe_last(series)

    assert result == 3.0
    assert isinstance(result, float)


def test_safe_last_returns_none_for_none():
    assert download.safe_last(None) is None


def test_safe_last_returns_none_for_empty_series():
    assert download.safe_last(pd.Series(dtype=float)) is None


def test_safe_last_returns_none_for_nan():
    series = pd.Series([1.0, float("nan")])

    assert download.safe_last(series) is None


def test_normalise_columns_returns_standard_dataframe():
    original = create_price_df()

    result = download.normalise_yfinance_columns(original)

    assert result is original
    assert list(result.columns) == [
        "Close",
        "High",
        "Low",
        "Volume",
    ]


def test_normalise_yfinance_multiindex_columns():
    original = create_price_df()
    original.columns = pd.MultiIndex.from_tuples(
        [
            ("Close", "TEST"),
            ("High", "TEST"),
            ("Low", "TEST"),
            ("Volume", "TEST"),
        ]
    )

    result = download.normalise_yfinance_columns(original)

    assert list(result.columns) == [
        "Close",
        "High",
        "Low",
        "Volume",
    ]


def test_normalise_columns_handles_none():
    assert download.normalise_yfinance_columns(None) is None


def test_safe_download_returns_valid_dataframe(monkeypatch):
    expected = create_price_df()

    monkeypatch.setattr(
        download.yf,
        "download",
        lambda *args, **kwargs: expected,
    )

    result = download.safe_download(
        "TEST",
        retries=1,
        sleep_seconds=0,
    )

    assert result is not None
    assert not result.empty
    assert set(["Close", "High", "Low", "Volume"]).issubset(
        result.columns
    )


def test_safe_download_removes_missing_close_rows(monkeypatch):
    expected = create_price_df()
    expected.loc[expected.index[-1], "Close"] = float("nan")

    monkeypatch.setattr(
        download.yf,
        "download",
        lambda *args, **kwargs: expected,
    )

    result = download.safe_download(
        "TEST",
        retries=1,
        sleep_seconds=0,
    )

    assert result is not None
    assert len(result) == len(expected) - 1
    assert result["Close"].notna().all()


def test_safe_download_returns_none_for_empty_download(monkeypatch):
    monkeypatch.setattr(
        download.yf,
        "download",
        lambda *args, **kwargs: pd.DataFrame(),
    )
    monkeypatch.setattr(
        download.time,
        "sleep",
        lambda *_: None,
    )

    result = download.safe_download(
        "TEST",
        retries=2,
        sleep_seconds=0,
    )

    assert result is None


def test_safe_download_returns_none_for_missing_columns(monkeypatch):
    invalid = pd.DataFrame(
        {
            "Close": [100.0],
            "Volume": [1_000_000],
        }
    )

    monkeypatch.setattr(
        download.yf,
        "download",
        lambda *args, **kwargs: invalid,
    )
    monkeypatch.setattr(
        download.time,
        "sleep",
        lambda *_: None,
    )

    result = download.safe_download(
        "TEST",
        retries=1,
        sleep_seconds=0,
    )

    assert result is None


def test_safe_download_returns_none_when_close_is_all_nan(monkeypatch):
    invalid = create_price_df()
    invalid["Close"] = float("nan")

    monkeypatch.setattr(
        download.yf,
        "download",
        lambda *args, **kwargs: invalid,
    )
    monkeypatch.setattr(
        download.time,
        "sleep",
        lambda *_: None,
    )

    result = download.safe_download(
        "TEST",
        retries=1,
        sleep_seconds=0,
    )

    assert result is None


def test_safe_download_handles_download_exception(monkeypatch):
    def raise_error(*args, **kwargs):
        raise RuntimeError("Download failed")

    monkeypatch.setattr(
        download.yf,
        "download",
        raise_error,
    )
    monkeypatch.setattr(
        download.time,
        "sleep",
        lambda *_: None,
    )

    result = download.safe_download(
        "TEST",
        retries=1,
        sleep_seconds=0,
    )

    assert result is None


def test_get_sp500_tickers_returns_normalised_symbols(monkeypatch):
    source = pd.DataFrame(
        {
            "Symbol": [
                "AAPL",
                "BRK.B",
            ]
        }
    )

    monkeypatch.setattr(
        download.pd,
        "read_csv",
        lambda *args, **kwargs: source,
    )

    result = download.get_sp500_tickers()

    assert result == [
        "AAPL",
        "BRK-B",
    ]


def test_get_sp500_tickers_uses_fallback_on_error(monkeypatch):
    def raise_error(*args, **kwargs):
        raise RuntimeError("S&P 500 source unavailable")

    monkeypatch.setattr(
        download.pd,
        "read_csv",
        raise_error,
    )

    result = download.get_sp500_tickers()

    assert result == download.TICKERS


def test_calculate_period_return():
    close = pd.Series(
        [100.0, 110.0, 121.0],
    )

    result = download.calculate_period_return(
        close,
        sessions=2,
    )

    assert result == pytest.approx(21.0)


def test_calculate_period_return_requires_history():
    close = pd.Series([100.0, 101.0])

    with pytest.raises(
        ValueError,
        match="Insufficient history",
    ):
        download.calculate_period_return(
            close,
            sessions=2,
        )


def test_get_market_context_returns_expected_structure(monkeypatch):
    market_data = create_price_df(periods=300)

    monkeypatch.setattr(
        download,
        "safe_download",
        lambda *args, **kwargs: market_data,
    )

    result = download.get_market_context()

    assert set(result) == {
        "spy_price",
        "spy_ma200",
        "spy_return",
        "spy_returns",
        "market_bull",
    }
    assert set(result["spy_returns"]) == {
        21,
        63,
        126,
        252,
    }
    assert result["spy_return"] == result["spy_returns"][63]
    assert result["market_bull"] is True


def test_get_market_context_rejects_empty_download(monkeypatch):
    monkeypatch.setattr(
        download,
        "safe_download",
        lambda *args, **kwargs: None,
    )

    with pytest.raises(
        ValueError,
        match="Unable to download market context",
    ):
        download.get_market_context()


def test_get_market_context_rejects_insufficient_history(monkeypatch):
    short_history = create_price_df(periods=100)

    monkeypatch.setattr(
        download,
        "safe_download",
        lambda *args, **kwargs: short_history,
    )

    with pytest.raises(
        ValueError,
        match="Insufficient",
    ):
        download.get_market_context()
