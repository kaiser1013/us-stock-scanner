from pathlib import Path

import pandas as pd
import pytest

from scanner.factor_validation import (
    DEFAULT_FACTORS,
    FactorDefinition,
    build_factor_validation_report,
    compare_factor_groups,
    export_factor_validation_report,
    validate_by_regime,
    validate_factor,
    validate_factor_combinations,
)


@pytest.fixture
def observations() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "SignalDate": pd.date_range("2024-01-02", periods=8, freq="B"),
            "Return": [0.02, -0.01, 0.03, -0.02, 0.01, 0.04, -0.01, 0.02],
            "MarketRegime": ["BULL", "BULL", "NEUTRAL", "BEAR", "BULL", "NEUTRAL", "BEAR", "BULL"],
            "RegimeScore": [15, 15, 7, 0, 15, 7, 0, 15],
            "RSComposite": [12.0, -2.0, 5.0, -8.0, 20.0, 1.0, -1.0, 3.0],
            "Breakout55": [True, False, True, False, True, True, False, True],
            "DistanceToHigh55": [1.0, -2.0, 0.5, -5.0, 2.0, 0.1, -1.0, 0.2],
        }
    )


@pytest.fixture
def benchmark(observations: pd.DataFrame) -> pd.Series:
    return pd.Series(0.005, index=pd.DatetimeIndex(observations["SignalDate"]))


def test_factor_definition_supports_comparison_operators(observations: pd.DataFrame) -> None:
    factor = FactorDefinition("PositiveRS", "RSComposite", ">", 0)
    assert factor.mask(observations).tolist() == [True, False, True, False, True, True, False, True]


def test_factor_definition_rejects_unknown_operator(observations: pd.DataFrame) -> None:
    factor = FactorDefinition("Bad", "RSComposite", "contains", 0)
    with pytest.raises(ValueError, match="Unsupported factor operator"):
        factor.mask(observations)


def test_validate_factor_records_sample_period_and_metrics(
    observations: pd.DataFrame,
    benchmark: pd.Series,
) -> None:
    result = validate_factor(
        observations,
        FactorDefinition("PositiveRS", "RSComposite", ">", 0),
        benchmark,
    )
    assert result.sample_size == 5
    assert result.start_date == pd.Timestamp("2024-01-02")
    assert result.end_date == pd.Timestamp("2024-01-11")
    assert result.win_rate == pytest.approx(1.0)
    assert result.total_return == pytest.approx((1.02 * 1.03 * 1.01 * 1.04 * 1.02) - 1)
    assert result.benchmark_return == pytest.approx((1.005**5) - 1)
    assert result.alpha == pytest.approx(result.total_return - result.benchmark_return)


def test_compare_factor_groups_has_baseline_on_and_off(
    observations: pd.DataFrame,
) -> None:
    report = compare_factor_groups(
        observations,
        FactorDefinition("Breakout", "Breakout55", "==", True),
    )
    assert report["group"].tolist() == ["baseline", "factor_on", "factor_off"]
    assert report["sample_size"].tolist() == [8, 5, 3]


def test_validate_factor_combinations_uses_logical_and(
    observations: pd.DataFrame,
) -> None:
    factors = [
        FactorDefinition("PositiveRS", "RSComposite", ">", 0),
        FactorDefinition("Breakout", "Breakout55", "==", True),
    ]
    report = validate_factor_combinations(observations, factors)
    assert len(report) == 1
    assert report.loc[0, "factor_name"] == "PositiveRS + Breakout"
    assert report.loc[0, "sample_size"] == 5


def test_validate_by_regime_always_reports_three_regimes(
    observations: pd.DataFrame,
) -> None:
    report = validate_by_regime(observations)
    assert report["group"].tolist() == ["BULL", "NEUTRAL", "BEAR"]
    assert report["sample_size"].tolist() == [4, 2, 2]


def test_empty_factor_selection_returns_zero_sample(observations: pd.DataFrame) -> None:
    result = validate_factor(
        observations,
        FactorDefinition("Impossible", "RSComposite", ">", 1_000),
    )
    assert result.sample_size == 0
    assert result.start_date is None
    assert result.total_return == 0.0


def test_missing_required_columns_are_rejected(observations: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_factor(
            observations.drop(columns="RegimeScore"),
            FactorDefinition("Breakout", "Breakout55", "==", True),
        )


def test_missing_benchmark_date_is_rejected(
    observations: pd.DataFrame,
    benchmark: pd.Series,
) -> None:
    incomplete = benchmark.iloc[:-1]
    with pytest.raises(ValueError, match="Missing benchmark returns"):
        validate_factor(
            observations,
            FactorDefinition("All", "RSComposite", ">", -1_000),
            incomplete,
        )


def test_build_report_contains_all_required_sections(
    observations: pd.DataFrame,
) -> None:
    report = build_factor_validation_report(observations, DEFAULT_FACTORS)
    assert set(report) == {
        "Individual Factors",
        "Factor Comparisons",
        "Factor Combinations",
        "Regime Analysis",
    }
    assert len(report["Individual Factors"]) == 4
    assert len(report["Factor Comparisons"]) == 12
    assert len(report["Factor Combinations"]) == 11
    assert len(report["Regime Analysis"]) == 15


def test_export_report_to_csv_directory(
    observations: pd.DataFrame,
    tmp_path: Path,
) -> None:
    report = build_factor_validation_report(observations, DEFAULT_FACTORS)
    destination = export_factor_validation_report(report, tmp_path / "factor_report")
    assert destination.is_dir()
    assert (destination / "individual_factors.csv").exists()
    assert (destination / "factor_comparisons.csv").exists()


def test_export_report_to_excel(
    observations: pd.DataFrame,
    tmp_path: Path,
) -> None:
    pytest.importorskip("openpyxl")
    report = build_factor_validation_report(observations, DEFAULT_FACTORS)
    destination = export_factor_validation_report(report, tmp_path / "factor_report.xlsx")
    assert destination.exists()
    workbook = pd.ExcelFile(destination, engine="openpyxl")
    assert set(workbook.sheet_names) == set(report)


def test_invalid_periods_per_year_is_rejected(observations: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="periods_per_year must be positive"):
        validate_factor(
            observations,
            FactorDefinition("PositiveRS", "RSComposite", ">", 0),
            periods_per_year=0,
        )
