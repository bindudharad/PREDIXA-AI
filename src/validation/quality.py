headerimport pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from src.validation.schema import OHLCVSchema
logger = logging.getLogger(__name__)

class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class QualityIssue:
    severity: Severity
    check_name: str
    message: str
    symbol: Optional[str] = None
    timestamp: Optional[pd.Timestamp] = None
    row_index: Optional[int] = None
    details: Optional[Dict[str, Any]] = None

@dataclass
class QualityReport:
    symbol: str
    total_rows: int
    issues: List[QualityIssue]
    passed: bool
    score: float
    def get_issues_by_severity(self, severity): return [i for i in self.issues if i.severity == severity]
    def has_critical(self): return any(i.severity == Severity.CRITICAL for i in self.issues)
    def has_errors(self): return any(i.severity == Severity.ERROR for i in self.issues)

class OHLCVQualityChecker:
    def __init__(self, max_gap_days=5, max_price_change_pct=0.50, max_volume_spike=100.0, min_volume=1, min_price=0.01, max_price=10000.0, allow_weekends=False, trading_hours_only=True):
        self.max_gap_days = max_gap_days
        self.max_price_change_pct = max_price_change_pct
        self.max_volume_spike = max_volume_spike
        self.min_volume = min_volume
        self.min_price = min_price
        self.max_price = max_price
        self.allow_weekends = allow_weekends
        self.trading_hours_only = trading_hours_only

    def check(self, df, symbol="UNKNOWN"):
        issues = []
        issues.extend(self._check_schema(df, symbol))
        if df.empty: return QualityReport(symbol=symbol, total_rows=0, issues=issues, passed=False, score=0.0)
        issues.extend(self._check_timestamps(df, symbol))
        issues.extend(self._check_duplicates(df, symbol))
        issues.extend(self._check_gaps(df, symbol))
        issues.extend(self._check_price_ranges(df, symbol))
        issues.extend(self._check_price_continuity(df, symbol))
        issues.extend(self._check_volume(df, symbol))
        issues.extend(self._check_ohlc_consistency(df, symbol))
        issues.extend(self._check_outliers(df, symbol))
        issues.extend(self._check_corporate_actions(df, symbol))
        score = self._calculate_score(issues, len(df))
        passed = not any(i.severity in [Severity.CRITICAL, Severity.ERROR] for i in issues)
        return QualityReport(symbol=symbol, total_rows=len(df), issues=issues, passed=passed, score=score)

    def _check_schema(self, df, symbol):
        issues = []
        required_cols = ["symbol", "timestamp", "open", "high", "low", "close", "volume"]
        for col in required_cols:
            if col not in df.columns:
                issues.append(QualityIssue(severity=Severity.CRITICAL, check_name="schema", message="Missing required column: " + col, symbol=symbol))
        if "symbol" in df.columns and df["symbol"].nunique() > 1:
            issues.append(QualityIssue(severity=Severity.WARNING, check_name="schema", message="Multiple symbols in dataframe: " + str(df["symbol"].unique()), symbol=symbol))
        return issues

    def _check_timestamps(self, df, symbol):
        issues = []
        if "timestamp" not in df.columns: return issues
        null_ts = df["timestamp"].isna().sum()
        if null_ts > 0:
            issues.append(QualityIssue(severity=Severity.CRITICAL, check_name="timestamps", message=str(null_ts) + " null timestamps found", symbol=symbol, details={"null_count": int(null_ts)}))
        if not df["timestamp"].is_monotonic_increasing:
            issues.append(QualityIssue(severity=Severity.ERROR, check_name="timestamps", message="Timestamps are not monotonically increasing", symbol=symbol))
        if hasattr(df["timestamp"].dtype, "tz") and df["timestamp"].dt.tz is not None:
            tzs = df["timestamp"].dt.tz.unique()
            if len(tzs) > 1:
                issues.append(QualityIssue(severity=Severity.WARNING, check_name="timestamps", message="Mixed timezones: " + str(tzs), symbol=symbol))
        now = pd.Timestamp.now(tz="UTC")
        future = df[df["timestamp"] > now]
        if len(future) > 0:
            issues.append(QualityIssue(severity=Severity.WARNING, check_name="timestamps", message=str(len(future)) + " rows with future timestamps", symbol=symbol, details={"future_count": len(future)}))
        if not self.allow_weekends:
            weekend = df[df["timestamp"].dt.dayofweek >= 5]
            if len(weekend) > 0:
                issues.append(QualityIssue(severity=Severity.INFO, check_name="timestamps", message=str(len(weekend)) + " rows on weekends", symbol=symbol, details={"weekend_count": len(weekend)}))
        return issues

    def _check_duplicates(self, df, symbol):
        issues = []
        if "timestamp" not in df.columns: return issues
        dup_mask = df.duplicated(subset=["timestamp"], keep=False)
        dup_count = dup_mask.sum()
        if dup_count > 0:
            dup_timestamps = df[dup_mask]["timestamp"].unique()
            issues.append(QualityIssue(severity=Severity.ERROR, check_name="duplicates", message=str(dup_count) + " duplicate timestamp rows (" + str(len(dup_timestamps)) + " unique timestamps)", symbol=symbol, details={"duplicate_rows": int(dup_count), "unique_timestamps": int(len(dup_timestamps))}))
        return issues

    def _check_gaps(self, df, symbol):
        issues = []
        if "timestamp" not in df.columns or len(df) < 2: return issues
        df_sorted = df.sort_values("timestamp").reset_index(drop=True)
        diffs = df_sorted["timestamp"].diff().dropna()
        expected_freq = pd.Timedelta(days=1)
        gap_mask = diffs > expected_freq * self.max_gap_days
        gaps = diffs[gap_mask]
        if len(gaps) > 0:
            issues.append(QualityIssue(severity=Severity.WARNING, check_name="gaps", message=str(len(gaps)) + " gaps > " + str(self.max_gap_days) + " days found", symbol=symbol, details={"gap_count": len(gaps), "max_gap_days": float(gaps.max() / pd.Timedelta(days=1)), "gap_dates": [str(g) for g in gaps.index[:10]]}))
        return issues

    def _check_price_ranges(self, df, symbol):
        issues = []
        for col in ["open", "high", "low", "close"]:
            if col not in df.columns: continue
            nulls = df[col].isna().sum()
            if nulls > 0:
                issues.append(QualityIssue(severity=Severity.CRITICAL, check_name="price_ranges", message=str(nulls) + " null values in " + col, symbol=symbol, details={"column": col, "null_count": int(nulls)}))
            below_min = (df[col] < self.min_price).sum()
            above_max = (df[col] > self.max_price).sum()
            if below_min > 0:
                issues.append(QualityIssue(severity=Severity.WARNING, check_name="price_ranges", message=str(below_min) + " " + col + " prices below minimum " + str(self.min_price), symbol=symbol, details={"column": col, "below_min": int(below_min)}))
            if above_max > 0:
                issues.append(QualityIssue(severity=Severity.WARNING, check_name="price_ranges", message=str(above_max) + " " + col + " prices above maximum " + str(self.max_price), symbol=symbol, details={"column": col, "above_max": int(above_max)}))
        return issues

    def _check_price_continuity(self, df, symbol):
        issues = []
        if "close" not in df.columns or len(df) < 2: return issues
        df_sorted = df.sort_values("timestamp").reset_index(drop=True)
        returns = df_sorted["close"].pct_change().dropna()
        extreme_mask = returns.abs() > self.max_price_change_pct
        extreme_count = extreme_mask.sum()
        if extreme_count > 0:
            extreme_returns = returns[extreme_mask]
            issues.append(QualityIssue(severity=Severity.WARNING, check_name="price_continuity", message=str(extreme_count) + " price moves > " + str(self.max_price_change_pct*100) + "% detected", symbol=symbol, details={"extreme_count": int(extreme_count), "max_move_pct": float(extreme_returns.abs().max() * 100), "max_move_date": str(extreme_returns.abs().idxmax()) if len(extreme_returns) > 0 else None}))
        zero_prices = (df_sorted["close"] <= 0).sum()
        if zero_prices > 0:
            issues.append(QualityIssue(severity=Severity.CRITICAL, check_name="price_continuity", message=str(zero_prices) + " zero or negative close prices", symbol=symbol))
        return issues

    def _check_volume(self, df, symbol):
        issues = []
        if "volume" not in df.columns: return issues
        neg_vol = (df["volume"] < 0).sum()
        if neg_vol > 0:
            issues.append(QualityIssue(severity=Severity.ERROR, check_name="volume", message=str(neg_vol) + " negative volume entries", symbol=symbol))
        zero_vol = (df["volume"] == 0).sum()
        if zero_vol > 0:
            issues.append(QualityIssue(severity=Severity.WARNING, check_name="volume", message=str(zero_vol) + " zero volume entries", symbol=symbol))
        if len(df) > 10:
            vol_median = df["volume"].median()
            if vol_median > 0:
                spike_mask = df["volume"] > vol_median * self.max_volume_spike
                spike_count = spike_mask.sum()
                if spike_count > 0:
                    issues.append(QualityIssue(severity=Severity.INFO, check_name="volume", message=str(spike_count) + " volume spikes > " + str(self.max_volume_spike) + "x median", symbol=symbol, details={"spike_count": int(spike_count), "median_volume": float(vol_median)}))
        return issues

    def _check_ohlc_consistency(self, df, symbol):
        issues = []
        required = ["open", "high", "low", "close"]
        if not all(c in df.columns for c in required): return issues
        invalid_hl = (df["high"] < df["low"]).sum()
        if invalid_hl > 0:
            issues.append(QualityIssue(severity=Severity.ERROR, check_name="ohlc_consistency", message=str(invalid_hl) + " rows where High < Low", symbol=symbol))
        invalid_ho = (df["high"] < df["open"]).sum()
        invalid_hc = (df["high"] < df["close"]).sum()
        if invalid_ho > 0 or invalid_hc > 0:
            issues.append(QualityIssue(severity=Severity.ERROR, check_name="ohlc_consistency", message=str(invalid_ho) + " rows High < Open, " + str(invalid_hc) + " rows High < Close", symbol=symbol))
        invalid_lo = (df["low"] > df["open"]).sum()
        invalid_lc = (df["low"] > df["close"]).sum()
        if invalid_lo > 0 or invalid_lc > 0:
            issues.append(QualityIssue(severity=Severity.ERROR, check_name="ohlc_consistency", message=str(invalid_lo) + " rows Low > Open, " + str(invalid_lc) + " rows Low > Close", symbol=symbol))
        return issues

    def _check_outliers(self, df, symbol):
        issues = []
        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns: continue
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            if IQR == 0: continue
            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            outlier_count = len(outliers)
            if outlier_count > 0:
                issues.append(QualityIssue(severity=Severity.INFO, check_name="outliers", message=str(outlier_count) + " statistical outliers in " + col + " (3x IQR)", symbol=symbol, details={"column": col, "outlier_count": outlier_count, "lower_bound": float(lower_bound), "upper_bound": float(upper_bound)}))
        return issues

    def _check_corporate_actions(self, df, symbol):
        issues = []
        if "close" not in df.columns or len(df) < 2: return issues
        df_sorted = df.sort_values("timestamp").reset_index(drop=True)
        returns = df_sorted["close"].pct_change().dropna()
        large_drops = returns[returns < -0.20]
        large_gains = returns[returns > 0.50]
        if len(large_drops) > 0:
            issues.append(QualityIssue(severity=Severity.INFO, check_name="corporate_actions", message=str(len(large_drops)) + " drops > 20% - possible unadjusted splits/dividends", symbol=symbol, details={"drop_count": len(large_drops), "max_drop_pct": float(large_drops.min() * 100)}))
        if len(large_gains) > 0:
            issues.append(QualityIssue(severity=Severity.INFO, check_name="corporate_actions", message=str(len(large_gains)) + " gains > 50% - possible unadjusted reverse splits", symbol=symbol, details={"gain_count": len(large_gains), "max_gain_pct": float(large_gains.max() * 100)}))
        return issues

    def _calculate_score(self, issues, total_rows):
        if total_rows == 0: return 0.0
        weights = {Severity.CRITICAL: 1.0, Severity.ERROR: 0.5, Severity.WARNING: 0.1, Severity.INFO: 0.01}
        penalty = sum(weights.get(i.severity, 0) for i in issues)
        normalized_penalty = min(penalty / max(total_rows / 100, 1), 1.0)
        return max(1.0 - normalized_penalty, 0.0)


def validate_ohlcv_dataframe(df, symbol="UNKNOWN", **checker_kwargs):
    checker = OHLCVQualityChecker(**checker_kwargs)
    return checker.check(df, symbol)

def validate_and_clean(df, symbol="UNKNOWN", drop_duplicates=True, fill_small_gaps=True, max_gap_fill_days=3, **checker_kwargs):
    checker = OHLCVQualityChecker(**checker_kwargs)
    report = checker.check(df, symbol)
    cleaned = df.copy()
    if drop_duplicates and "timestamp" in cleaned.columns:
        before = len(cleaned)
        cleaned = cleaned.drop_duplicates(subset=["timestamp"], keep="first").reset_index(drop=True)
        dropped = before - len(cleaned)
        if dropped > 0: logger.info("Dropped " + str(dropped) + " duplicate rows for " + symbol)
    if fill_small_gaps and "timestamp" in cleaned.columns and len(cleaned) > 1:
        cleaned = _fill_small_gaps(cleaned, max_gap_fill_days)
    final_report = checker.check(cleaned, symbol)
    return cleaned, final_report

def _fill_small_gaps(df, max_gap_days):
    if "timestamp" not in df.columns: return df
    df_sorted = df.sort_values("timestamp").reset_index(drop=True)
    full_range = pd.date_range(start=df_sorted["timestamp"].min(), end=df_sorted["timestamp"].max(), freq="D")
    df_indexed = df_sorted.set_index("timestamp").reindex(full_range)
    gaps = df_indexed.index.to_series().diff().dt.days > 1
    gap_starts = df_indexed.index[gaps]
    for gs in gap_starts:
        gap_end = gs + pd.Timedelta(days=max_gap_days)
        mask = (df_indexed.index > gs) & (df_indexed.index <= gap_end)
        if mask.any(): df_indexed.loc[mask] = df_indexed.loc[mask].ffill()
    df_cleaned = df_indexed.dropna(subset=["open", "high", "low", "close", "volume"], how="all")
    df_cleaned = df_cleaned.reset_index().rename(columns={"index": "timestamp"})
    return df_cleaned


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dates = pd.date_range("2024-01-01", periods=100, freq="D", tz="US/Eastern")
    test_df = pd.DataFrame({
        "symbol": "TEST",
        "timestamp": dates,
        "open": 100 + np.random.randn(100).cumsum(),
        "high": 100 + np.random.randn(100).cumsum() + 1,
        "low": 100 + np.random.randn(100).cumsum() - 1,
        "close": 100 + np.random.randn(100).cumsum(),
        "volume": np.random.randint(1000000, 10000000, 100)
    })
    test_df["high"] = test_df[["open", "high", "close"]].max(axis=1)
    test_df["low"] = test_df[["open", "low", "close"]].min(axis=1)
    test_df.loc[10, "high"] = 50
    test_df.loc[20, "volume"] = -1000
    test_df = pd.concat([test_df, test_df.iloc[[30]]], ignore_index=True)
    report = validate_ohlcv_dataframe(test_df, "TEST")
    print("Quality Score:", report.score)
    print("Passed:", report.passed)
    print("Issues:", len(report.issues))
    for issue in report.issues:
        print("  [" + issue.severity.value + "] " + issue.check_name + ": " + issue.message)
