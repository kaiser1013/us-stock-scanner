import math

import numpy as np
import pandas as pd
import pytest

from scanner.benchmark import (
    ACTIVE_RETURN_COLUMN,
    BENCHMARK_COLUMN,
    BENCHMARK_RETURN_COLUMN,
    PORTFOLIO_COLUMN,
    PORTFOLIO_RETURN_COLUMN,
    BenchmarkConfig,
    BenchmarkResult,
    align_return_series,
    align_value_series,
    build_benchmark_metrics,
    calculate_beta,
    calculate_information_ratio,
    calculate_return_series,
    calculate_total_return,
    calculate_tracking_error,
)


def series(values, dates=None):
    index = (
        dates
        if dates is not None
        else pd.date_range(
            "2025-01-02",
            periods=len(values),
            freq="B",
        )
    )

    return pd.Series(
        values,
        index=index,
        dtype=float,
    )


def return_frame(
    portfolio,
    benchmark,
):
    frame = pd.DataFrame(
        {
            PORTFOLIO_RETURN_COLUMN: portfolio,
            BENCHMARK_RETURN_COLUMN: benchmark,
        },
        index=pd.date_range(
            "2025-01-02",
            periods=len(portfolio),
            freq="B",
        ),
    )

    frame[ACTIVE_RETURN_COLUMN] = (
        frame[PORTFOLIO_RETURN_COLUMN]
        - frame[BENCHMARK_RETURN_COLUMN]
    )

    return frame


def test_config_rejects_invalid_values():
    with pytest.raises(ValueError):
        BenchmarkConfig(
            periods_per_year=0,
        )

    with pytest.raises(ValueError):
        BenchmarkConfig(
            minimum_observations=1,
        )


def test_align_value_series_uses_common_dates_and_sorts():
    portfolio = series(
        [103, 100, 102],
        pd.to_datetime(
            [
                "2025-01-06",
                "2025-01-02",
                "2025-01-03",
            ]
        ),
    )

    benchmark = series(
        [200, 202, 204],
        pd.to_datetime(
            [
                "2025-01-02",
                "2025-01-03",
                "2025-01-07",
            ]
        ),
    )

    aligned = align_value_series(
        portfolio,
        benchmark,
    )

    assert list(aligned.index) == list(
        pd.to_datetime(
            [
                "2025-01-02",
                "2025-01-03",
            ]
        )
    )

    assert list(aligned.columns) == [
        PORTFOLIO_COLUMN,
        BENCHMARK_COLUMN,
    ]


def test_align_value_series_drops_missing_values():
    aligned = align_value_series(
        series(
            [100, np.nan, 103]
        ),
        series(
            [200, 201, 202]
        ),
    )

    assert len(aligned) == 2
    assert not aligned.isna().any().any()


def test_align_value_series_rejects_no_overlap():
    portfolio = series(
        [100, 101],
        pd.to_datetime(
            [
                "2025-01-02",
                "2025-01-03",
            ]
        ),
    )

    benchmark = series(
        [200, 201],
        pd.to_datetime(
            [
                "2025-02-03",
                "2025-02-04",
            ]
        ),
    )

    with pytest.raises(ValueError):
        align_value_series(
            portfolio,
            benchmark,
        )


def test_align_value_series_normalises_timezone_and_duplicate_dates():
    portfolio = pd.Series(
        [100, 101],
        index=pd.to_datetime(
            [
                "2025-01-02 10:00",
                "2025-01-02 16:00",
            ],
            utc=True,
        ),
    )

    benchmark = series(
        [200],
        pd.to_datetime(
            ["2025-01-02"]
        ),
    )

    aligned = align_value_series(
        portfolio,
        benchmark,
    )

    assert len(aligned) == 1

    assert (
        aligned.iloc[0][PORTFOLIO_COLUMN]
        == 101
    )


def test_calculate_return_series_returns_required_columns():
    aligned = pd.DataFrame(
        {
            PORTFOLIO_COLUMN: [100, 105, 110],
            BENCHMARK_COLUMN: [200, 202, 204],
        },
        index=pd.date_range(
            "2025-01-02",
            periods=3,
            freq="B",
        ),
    )

    returns = calculate_return_series(
        aligned
    )

    assert list(returns.columns) == [
        PORTFOLIO_RETURN_COLUMN,
        BENCHMARK_RETURN_COLUMN,
        ACTIVE_RETURN_COLUMN,
    ]

    assert (
        returns.iloc[0][PORTFOLIO_RETURN_COLUMN]
        == pytest.approx(0.05)
    )


def test_beta_equals_two_for_double_benchmark_returns():
    benchmark = [
        0.01,
        -0.02,
        0.03,
        -0.01,
    ]

    portfolio = [
        x * 2
        for x in benchmark
    ]

    beta = calculate_beta(
        return_frame(
            portfolio,
            benchmark,
        )
    )

    assert beta == pytest.approx(2.0)


def test_beta_rejects_zero_benchmark_variance():
    returns = return_frame(
        [0.01, 0.02, 0.03],
        [0.01, 0.01, 0.01],
    )

    with pytest.raises(ValueError):
        calculate_beta(
            returns
        )


def test_tracking_error_matches_manual_calculation():
    returns = return_frame(
        [0.02, 0.01, -0.01],
        [0.01, 0.015, -0.005],
    )

    active = np.array(
        [
            0.01,
            -0.005,
            -0.005,
        ]
    )

    expected = (
        active.std(ddof=1)
        * math.sqrt(252)
    )

    assert (
        calculate_tracking_error(
            returns
        )
        == pytest.approx(expected)
    )


def test_information_ratio_matches_manual_calculation():
    returns = return_frame(
        [0.02, 0.01, -0.01],
        [0.01, 0.015, -0.005],
    )

    active = np.array(
        [
            0.01,
            -0.005,
            -0.005,
        ]
    )

    expected = (
        active.mean()
        * 252
        /
        (
            active.std(ddof=1)
            * math.sqrt(252)
        )
    )

    assert (
        calculate_information_ratio(
            returns
        )
        == pytest.approx(expected)
    )


def test_information_ratio_is_zero_for_identical_returns():
    returns = return_frame(
        [0.01, -0.02, 0.03],
        [0.01, -0.02, 0.03],
    )

    assert (
        calculate_information_ratio(
            returns
        )
        == pytest.approx(0.0)
    )


def test_total_return_is_percentage_change():
    result = calculate_total_return(
        series(
            [100, 105, 110]
        )
    )

    assert result == pytest.approx(10.0)


def test_build_benchmark_metrics_returns_expected_result():
    portfolio = series(
        [100, 102, 101, 106, 110]
    )

    benchmark = series(
        [200, 201, 202, 204, 206]
    )

    result = build_benchmark_metrics(
        portfolio,
        benchmark,
    )

    assert isinstance(
        result,
        BenchmarkResult,
    )

    assert result.observations == 4

    assert (
        result.portfolio_return
        == pytest.approx(10.0)
    )

    assert (
        result.benchmark_return
        == pytest.approx(3.0)
    )

    assert (
        result.alpha
        == pytest.approx(7.0)
    )

    assert math.isfinite(
        result.beta
    )

    assert math.isfinite(
        result.tracking_error
    )

    assert math.isfinite(
        result.information_ratio
    )

def test_calculate_return_series_rejects_missing_columns():
    with pytest.raises(ValueError):
        calculate_return_series(
            pd.DataFrame(
                {
                    PORTFOLIO_COLUMN: [100, 101]
                }
            )
        )


def test_calculate_return_series_rejects_non_positive_values():
    aligned = pd.DataFrame(
        {
            PORTFOLIO_COLUMN: [100, 0],
            BENCHMARK_COLUMN: [200, 201],
        },
        index=pd.date_range(
            "2025-01-02",
            periods=2,
            freq="B",
        ),
    )

    with pytest.raises(ValueError):
        calculate_return_series(
            aligned
        )


def test_align_return_series_calculates_active_return():
    portfolio = series(
        [0.01, 0.02, -0.01]
    )

    benchmark = series(
        [0.005, 0.01, -0.005]
    )

    aligned = align_return_series(
        portfolio,
        benchmark,
    )

    assert (
        aligned.iloc[0][ACTIVE_RETURN_COLUMN]
        == pytest.approx(0.005)
    )


def test_tracking_error_supports_custom_annualisation():
    returns = return_frame(
        [0.02, 0.01, -0.01],
        [0.01, 0.015, -0.005],
    )

    active = np.array(
        [
            0.01,
            -0.005,
            -0.005,
        ]
    )

    expected = (
        active.std(ddof=1)
        * math.sqrt(12)
    )

    assert (
        calculate_tracking_error(
            returns,
            12,
        )
        == pytest.approx(expected)
    )


def test_information_ratio_rejects_zero_tracking_error_with_active_return():
    returns = return_frame(
        [0.02, 0.02, 0.02],
        [0.01, 0.01, 0.01],
    )

    with pytest.raises(ValueError):
        calculate_information_ratio(
            returns,
        )


def test_total_return_rejects_short_series():
    with pytest.raises(ValueError):
        calculate_total_return(
            series([100])
        )


def test_total_return_rejects_non_positive_values():
    with pytest.raises(ValueError):
        calculate_total_return(
            series([100, 0])
        )


def test_build_benchmark_metrics_uses_only_aligned_dates():
    portfolio = series(
        [100, 102, 105, 110],
        pd.to_datetime(
            [
                "2025-01-02",
                "2025-01-03",
                "2025-01-06",
                "2025-01-07",
            ]
        ),
    )

    benchmark = series(
        [200, 201, 203, 206],
        pd.to_datetime(
            [
                "2025-01-02",
                "2025-01-03",
                "2025-01-06",
                "2025-01-08",
            ]
        ),
    )

    result = build_benchmark_metrics(
        portfolio,
        benchmark,
    )

    assert (
        result.start_date
        == pd.Timestamp(
            "2025-01-02"
        )
    )

    assert (
        result.end_date
        == pd.Timestamp(
            "2025-01-06"
        )
    )

    assert result.observations == 2


def test_build_benchmark_metrics_enforces_minimum_observations():
    portfolio = series(
        [100, 101, 102]
    )

    benchmark = series(
        [200, 201, 202]
    )

    with pytest.raises(ValueError):
        build_benchmark_metrics(
            portfolio,
            benchmark,
            BenchmarkConfig(
                minimum_observations=3,
            ),
        )


def test_result_helpers_and_csv_export(tmp_path):
    result = BenchmarkResult(
        observations=3,
        start_date=pd.Timestamp(
            "2025-01-02"
        ),
        end_date=pd.Timestamp(
            "2025-01-06"
        ),
        portfolio_return=5.0,
        benchmark_return=3.0,
        alpha=2.0,
        beta=1.1,
        tracking_error=0.08,
        information_ratio=0.5,
    )

    payload = result.to_dict()

    assert (
        payload["beta"]
        == pytest.approx(1.1)
    )

    frame = result.to_frame()

    assert list(frame.columns) == list(
        payload.keys()
    )

    output = result.export(
        tmp_path / "benchmark.csv"
    )

    assert output.exists()


def test_result_export_rejects_unknown_extension(tmp_path):
    result = BenchmarkResult(
        observations=2,
        start_date=pd.Timestamp(
            "2025-01-02"
        ),
        end_date=pd.Timestamp(
            "2025-01-03"
        ),
        portfolio_return=1.0,
        benchmark_return=0.5,
        alpha=0.5,
        beta=1.0,
        tracking_error=0.1,
        information_ratio=0.2,
    )

    with pytest.raises(ValueError):
        result.export(
            tmp_path / "benchmark.txt"
        )

def test_beta_returns_float():
    returns = return_frame(
        [0.02, 0.01, -0.01],
        [0.01, 0.005, -0.005],
    )

    result = calculate_beta(
        returns
    )

    assert isinstance(
        result,
        float,
    )

    assert math.isfinite(
        result
    )


def test_tracking_error_returns_float():
    returns = return_frame(
        [0.02, 0.01, -0.01],
        [0.01, 0.015, -0.005],
    )

    result = calculate_tracking_error(
        returns
    )

    assert isinstance(
        result,
        float,
    )

    assert math.isfinite(
        result
    )
