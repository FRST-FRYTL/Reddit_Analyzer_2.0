"""
Statistical analysis module for Reddit data.

This module provides comprehensive statistical analysis capabilities including
descriptive statistics, correlation analysis, hypothesis testing, and
distribution analysis for Reddit posts and comments.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Union
import numpy as np
import pandas as pd

from scipy import stats
from scipy.stats import (
    pearsonr,
    spearmanr,
    kendalltau,
    chi2_contingency,
    shapiro,
    ttest_ind,
    mannwhitneyu,
    kruskal,
)
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.stats.diagnostic import jarque_bera
import warnings

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


class StatisticalAnalyzer:
    """
    Comprehensive statistical analysis system for Reddit data.

    Provides descriptive statistics, correlation analysis, hypothesis testing,
    distribution analysis, and trend analysis capabilities.
    """

    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize the statistical analyzer.

        Args:
            confidence_level: Confidence level for statistical tests (default 0.95)
        """
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level

        logger.info(
            f"Statistical analyzer initialized with {confidence_level * 100}% confidence level"
        )

    def descriptive_statistics(
        self,
        data: Union[List[Dict[str, Any]], pd.DataFrame],
        columns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive descriptive statistics for numerical columns.

        Args:
            data: Data to analyze (list of dicts or DataFrame)
            columns: Specific columns to analyze (if None, analyzes all numerical columns)

        Returns:
            Dictionary with descriptive statistics for each column
        """
        # Convert to DataFrame if needed
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data.copy()

        if df.empty:
            return {}

        # Select numerical columns
        if columns is None:
            numerical_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        else:
            numerical_columns = [
                col
                for col in columns
                if col in df.columns
                and df[col].dtype in [np.number, "int64", "float64"]
            ]

        if not numerical_columns:
            return {"error": "No numerical columns found"}

        results = {}

        for column in numerical_columns:
            series = df[column].dropna()

            if len(series) == 0:
                results[column] = {"error": "No valid data"}
                continue

            # Basic descriptive statistics
            stats_dict = {
                "count": int(len(series)),
                "mean": float(series.mean()),
                "median": float(series.median()),
                "mode": (
                    float(series.mode().iloc[0]) if not series.mode().empty else None
                ),
                "std": float(series.std()),
                "var": float(series.var()),
                "min": float(series.min()),
                "max": float(series.max()),
                "range": float(series.max() - series.min()),
                "q1": float(series.quantile(0.25)),
                "q3": float(series.quantile(0.75)),
                "iqr": float(series.quantile(0.75) - series.quantile(0.25)),
                "skewness": float(series.skew()),
                "kurtosis": float(series.kurtosis()),
            }

            # Additional percentiles
            percentiles = [5, 10, 90, 95, 99]
            for p in percentiles:
                stats_dict[f"p{p}"] = float(series.quantile(p / 100))

            # Outlier detection using IQR method
            q1, q3 = stats_dict["q1"], stats_dict["q3"]
            iqr = stats_dict["iqr"]
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            outliers = series[(series < lower_bound) | (series > upper_bound)]
            stats_dict["outliers"] = {
                "count": len(outliers),
                "percentage": float(len(outliers) / len(series) * 100),
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound),
            }

            # Coefficient of variation
            if stats_dict["mean"] != 0:
                stats_dict["cv"] = float(stats_dict["std"] / abs(stats_dict["mean"]))
            else:
                stats_dict["cv"] = None

            # Distribution shape analysis
            stats_dict["distribution"] = self._analyze_distribution_shape(series)

            results[column] = stats_dict

        return results

    def correlation_analysis(
        self,
        data: Union[List[Dict[str, Any]], pd.DataFrame],
        columns: Optional[List[str]] = None,
        methods: List[str] = ["pearson", "spearman"],
    ) -> Dict[str, Any]:
        """
        Perform correlation analysis between numerical variables.

        Args:
            data: Data to analyze
            columns: Specific columns to include in correlation analysis
            methods: Correlation methods to use

        Returns:
            Dictionary with correlation matrices and significance tests
        """
        # Convert to DataFrame if needed
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data.copy()

        if df.empty:
            return {}

        # Select numerical columns
        if columns is None:
            numerical_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        else:
            numerical_columns = [col for col in columns if col in df.columns]

        if len(numerical_columns) < 2:
            return {
                "error": "Need at least 2 numerical columns for correlation analysis"
            }

        # Clean data
        clean_df = df[numerical_columns].dropna()

        if clean_df.empty:
            return {"error": "No valid data after removing missing values"}

        results = {
            "sample_size": len(clean_df),
            "variables": numerical_columns,
            "methods": {},
        }

        for method in methods:
            if method == "pearson":
                corr_matrix, p_values = self._pearson_correlation_matrix(clean_df)
            elif method == "spearman":
                corr_matrix, p_values = self._spearman_correlation_matrix(clean_df)
            elif method == "kendall":
                corr_matrix, p_values = self._kendall_correlation_matrix(clean_df)
            else:
                logger.warning(f"Unknown correlation method: {method}")
                continue

            # Find significant correlations
            significant_pairs = []
            n_vars = len(numerical_columns)

            for i in range(n_vars):
                for j in range(i + 1, n_vars):
                    var1, var2 = numerical_columns[i], numerical_columns[j]
                    corr_coef = corr_matrix.iloc[i, j]
                    p_value = p_values.iloc[i, j]

                    significant_pairs.append(
                        {
                            "variable1": var1,
                            "variable2": var2,
                            "correlation": float(corr_coef),
                            "p_value": float(p_value),
                            "significant": p_value < self.alpha,
                            "strength": self._interpret_correlation_strength(
                                abs(corr_coef)
                            ),
                        }
                    )

            # Sort by absolute correlation strength
            significant_pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)

            results["methods"][method] = {
                "correlation_matrix": corr_matrix.to_dict(),
                "p_value_matrix": p_values.to_dict(),
                "significant_correlations": significant_pairs,
                "summary": {
                    "total_pairs": len(significant_pairs),
                    "significant_pairs": sum(
                        1 for p in significant_pairs if p["significant"]
                    ),
                    "strong_correlations": sum(
                        1 for p in significant_pairs if abs(p["correlation"]) > 0.7
                    ),
                    "moderate_correlations": sum(
                        1
                        for p in significant_pairs
                        if 0.3 < abs(p["correlation"]) <= 0.7
                    ),
                },
            }

        return results

    def hypothesis_testing(
        self,
        data: Union[List[Dict[str, Any]], pd.DataFrame],
        tests: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Perform various hypothesis tests.

        Args:
            data: Data to analyze
            tests: List of test specifications, each containing test type and parameters

        Returns:
            Dictionary with test results
        """
        # Convert to DataFrame if needed
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data.copy()

        if df.empty:
            return {"error": "No data provided"}

        results = {}

        for i, test_spec in enumerate(tests):
            test_name = test_spec.get("name", f"test_{i}")
            test_type = test_spec.get("type")

            try:
                if test_type == "normality":
                    result = self._test_normality(df, test_spec)
                elif test_type == "two_sample_ttest":
                    result = self._two_sample_ttest(df, test_spec)
                elif test_type == "mann_whitney":
                    result = self._mann_whitney_test(df, test_spec)
                elif test_type == "chi_square":
                    result = self._chi_square_test(df, test_spec)
                elif test_type == "anova":
                    result = self._anova_test(df, test_spec)
                elif test_type == "kruskal_wallis":
                    result = self._kruskal_wallis_test(df, test_spec)
                else:
                    result = {"error": f"Unknown test type: {test_type}"}

                results[test_name] = result

            except Exception as e:
                logger.warning(f"Failed to perform test {test_name}: {e}")
                results[test_name] = {"error": str(e)}

        return results

    def time_series_analysis(
        self,
        data: Union[List[Dict[str, Any]], pd.DataFrame],
        timestamp_column: str,
        value_column: str,
        freq: str = "D",
    ) -> Dict[str, Any]:
        """
        Perform time series analysis on temporal data.

        Args:
            data: Data with timestamp and value columns
            timestamp_column: Name of timestamp column
            value_column: Name of value column to analyze
            freq: Frequency for resampling (D=daily, W=weekly, M=monthly)

        Returns:
            Time series analysis results
        """
        # Convert to DataFrame if needed
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data.copy()

        if (
            df.empty
            or timestamp_column not in df.columns
            or value_column not in df.columns
        ):
            return {"error": "Missing required columns"}

        try:
            # Prepare time series data
            df[timestamp_column] = pd.to_datetime(df[timestamp_column])
            df = df.sort_values(timestamp_column)
            df = df.set_index(timestamp_column)

            # Resample to specified frequency
            ts = df[value_column].resample(freq).sum()
            ts = ts.dropna()

            if len(ts) < 7:  # Need at least 7 periods for decomposition
                return {"error": "Insufficient time series data"}

            # Basic time series statistics
            results = {
                "summary": {
                    "start_date": str(ts.index.min()),
                    "end_date": str(ts.index.max()),
                    "periods": len(ts),
                    "frequency": freq,
                    "mean": float(ts.mean()),
                    "std": float(ts.std()),
                    "min": float(ts.min()),
                    "max": float(ts.max()),
                }
            }

            # Trend analysis
            results["trend"] = self._analyze_trend(ts)

            # Seasonal decomposition (if enough data)
            if len(ts) >= 14:  # Need at least 2 cycles for seasonal decomposition
                try:
                    decomposition = seasonal_decompose(ts, model="additive", period=7)

                    results["decomposition"] = {
                        "trend": decomposition.trend.dropna().to_dict(),
                        "seasonal": decomposition.seasonal.dropna().to_dict(),
                        "residual": decomposition.resid.dropna().to_dict(),
                        "seasonal_strength": float(
                            1 - decomposition.resid.var() / ts.var()
                        ),
                    }
                except Exception as e:
                    logger.warning(f"Seasonal decomposition failed: {e}")
                    results["decomposition"] = {"error": str(e)}

            # Autocorrelation analysis
            results["autocorrelation"] = self._analyze_autocorrelation(ts)

            # Stationarity tests
            results["stationarity"] = self._test_stationarity(ts)

            return results

        except Exception as e:
            logger.error(f"Time series analysis failed: {e}")
            return {"error": str(e)}

    def group_comparison(
        self,
        data: Union[List[Dict[str, Any]], pd.DataFrame],
        group_column: str,
        value_columns: List[str],
    ) -> Dict[str, Any]:
        """
        Compare groups across multiple metrics.

        Args:
            data: Data to analyze
            group_column: Column defining groups
            value_columns: Columns to compare across groups

        Returns:
            Group comparison results
        """
        # Convert to DataFrame if needed
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data.copy()

        if df.empty or group_column not in df.columns:
            return {"error": "Missing group column"}

        # Filter valid value columns
        valid_columns = [col for col in value_columns if col in df.columns]

        if not valid_columns:
            return {"error": "No valid value columns found"}

        results = {
            "group_column": group_column,
            "value_columns": valid_columns,
            "groups": {},
            "comparisons": {},
        }

        # Get unique groups
        groups = df[group_column].dropna().unique()

        if len(groups) < 2:
            return {"error": "Need at least 2 groups for comparison"}

        # Analyze each group
        for group in groups:
            group_data = df[df[group_column] == group]
            group_stats = {}

            for column in valid_columns:
                series = group_data[column].dropna()

                if len(series) > 0:
                    group_stats[column] = {
                        "count": len(series),
                        "mean": float(series.mean()),
                        "median": float(series.median()),
                        "std": float(series.std()),
                        "min": float(series.min()),
                        "max": float(series.max()),
                    }

            results["groups"][str(group)] = group_stats

        # Perform pairwise comparisons
        for column in valid_columns:
            column_comparisons = {}

            # Get data for each group
            group_data = {}
            for group in groups:
                group_series = df[df[group_column] == group][column].dropna()
                if len(group_series) > 0:
                    group_data[group] = group_series

            # Pairwise statistical tests
            group_names = list(group_data.keys())
            for i in range(len(group_names)):
                for j in range(i + 1, len(group_names)):
                    group1, group2 = group_names[i], group_names[j]
                    data1, data2 = group_data[group1], group_data[group2]

                    # T-test (assuming normality)
                    try:
                        t_stat, t_p = ttest_ind(data1, data2)
                        ttest_result = {
                            "statistic": float(t_stat),
                            "p_value": float(t_p),
                            "significant": t_p < self.alpha,
                        }
                    except Exception:
                        ttest_result = {"error": "T-test failed"}

                    # Mann-Whitney U test (non-parametric)
                    try:
                        u_stat, u_p = mannwhitneyu(
                            data1, data2, alternative="two-sided"
                        )
                        mannwhitney_result = {
                            "statistic": float(u_stat),
                            "p_value": float(u_p),
                            "significant": u_p < self.alpha,
                        }
                    except Exception:
                        mannwhitney_result = {"error": "Mann-Whitney test failed"}

                    comparison_key = f"{group1}_vs_{group2}"
                    column_comparisons[comparison_key] = {
                        "ttest": ttest_result,
                        "mann_whitney": mannwhitney_result,
                        "effect_size": self._calculate_effect_size(data1, data2),
                    }

            results["comparisons"][column] = column_comparisons

        return results

    def _analyze_distribution_shape(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze the shape and normality of a distribution."""
        # Normality tests
        normality_tests = {}

        if len(series) >= 8:
            try:
                shapiro_stat, shapiro_p = shapiro(series)
                normality_tests["shapiro"] = {
                    "statistic": float(shapiro_stat),
                    "p_value": float(shapiro_p),
                    "normal": shapiro_p > self.alpha,
                }
            except Exception:
                pass

        if len(series) >= 20:
            try:
                jb_stat, jb_p = jarque_bera(series)
                normality_tests["jarque_bera"] = {
                    "statistic": float(jb_stat),
                    "p_value": float(jb_p),
                    "normal": jb_p > self.alpha,
                }
            except Exception:
                pass

        # Distribution characteristics
        distribution = {
            "normality_tests": normality_tests,
            "likely_normal": any(
                test.get("normal", False) for test in normality_tests.values()
            ),
            "distribution_type": self._infer_distribution_type(series),
        }

        return distribution

    def _infer_distribution_type(self, series: pd.Series) -> str:
        """Infer the likely distribution type based on characteristics."""
        skewness = series.skew()
        kurtosis = series.kurtosis()

        if abs(skewness) < 0.5 and abs(kurtosis) < 0.5:
            return "approximately_normal"
        elif skewness > 1:
            return "right_skewed"
        elif skewness < -1:
            return "left_skewed"
        elif kurtosis > 3:
            return "heavy_tailed"
        elif kurtosis < -1:
            return "light_tailed"
        else:
            return "unknown"

    def _pearson_correlation_matrix(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Calculate Pearson correlation matrix with p-values."""
        n_vars = len(df.columns)
        corr_matrix = df.corr(method="pearson")
        p_values = pd.DataFrame(
            np.zeros((n_vars, n_vars)), index=df.columns, columns=df.columns
        )

        for i, col1 in enumerate(df.columns):
            for j, col2 in enumerate(df.columns):
                if i != j:
                    corr, p_val = pearsonr(df[col1].dropna(), df[col2].dropna())
                    p_values.iloc[i, j] = p_val
                else:
                    p_values.iloc[i, j] = 0.0

        return corr_matrix, p_values

    def _spearman_correlation_matrix(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Calculate Spearman correlation matrix with p-values."""
        n_vars = len(df.columns)
        corr_matrix = df.corr(method="spearman")
        p_values = pd.DataFrame(
            np.zeros((n_vars, n_vars)), index=df.columns, columns=df.columns
        )

        for i, col1 in enumerate(df.columns):
            for j, col2 in enumerate(df.columns):
                if i != j:
                    corr, p_val = spearmanr(df[col1].dropna(), df[col2].dropna())
                    p_values.iloc[i, j] = p_val
                else:
                    p_values.iloc[i, j] = 0.0

        return corr_matrix, p_values

    def _kendall_correlation_matrix(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Calculate Kendall tau correlation matrix with p-values."""
        n_vars = len(df.columns)
        corr_matrix = pd.DataFrame(
            np.zeros((n_vars, n_vars)), index=df.columns, columns=df.columns
        )
        p_values = pd.DataFrame(
            np.zeros((n_vars, n_vars)), index=df.columns, columns=df.columns
        )

        for i, col1 in enumerate(df.columns):
            for j, col2 in enumerate(df.columns):
                if i == j:
                    corr_matrix.iloc[i, j] = 1.0
                    p_values.iloc[i, j] = 0.0
                else:
                    corr, p_val = kendalltau(df[col1].dropna(), df[col2].dropna())
                    corr_matrix.iloc[i, j] = corr
                    p_values.iloc[i, j] = p_val

        return corr_matrix, p_values

    def _interpret_correlation_strength(self, correlation: float) -> str:
        """Interpret correlation strength."""
        abs_corr = abs(correlation)

        if abs_corr >= 0.9:
            return "very_strong"
        elif abs_corr >= 0.7:
            return "strong"
        elif abs_corr >= 0.5:
            return "moderate"
        elif abs_corr >= 0.3:
            return "weak"
        else:
            return "very_weak"

    def _test_normality(
        self, df: pd.DataFrame, test_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test normality of a variable."""
        column = test_spec.get("column")

        if column not in df.columns:
            return {"error": f"Column {column} not found"}

        series = df[column].dropna()

        if len(series) < 3:
            return {"error": "Insufficient data for normality test"}

        results = {"column": column, "sample_size": len(series)}

        # Shapiro-Wilk test
        if len(series) <= 5000:  # Shapiro-Wilk is limited to 5000 samples
            try:
                stat, p = shapiro(series)
                results["shapiro_wilk"] = {
                    "statistic": float(stat),
                    "p_value": float(p),
                    "is_normal": p > self.alpha,
                }
            except Exception:
                pass

        # Jarque-Bera test
        try:
            stat, p = jarque_bera(series)
            results["jarque_bera"] = {
                "statistic": float(stat),
                "p_value": float(p),
                "is_normal": p > self.alpha,
            }
        except Exception:
            pass

        return results

    def _two_sample_ttest(
        self, df: pd.DataFrame, test_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform two-sample t-test."""
        column = test_spec.get("column")
        group_column = test_spec.get("group_column")
        groups = test_spec.get("groups", [])

        if len(groups) != 2:
            return {"error": "Need exactly 2 groups for t-test"}

        group1_data = df[df[group_column] == groups[0]][column].dropna()
        group2_data = df[df[group_column] == groups[1]][column].dropna()

        if len(group1_data) < 2 or len(group2_data) < 2:
            return {"error": "Insufficient data in groups"}

        stat, p = ttest_ind(group1_data, group2_data)

        return {
            "test_type": "two_sample_ttest",
            "groups": groups,
            "group1_size": len(group1_data),
            "group2_size": len(group2_data),
            "statistic": float(stat),
            "p_value": float(p),
            "significant": p < self.alpha,
            "effect_size": self._calculate_effect_size(group1_data, group2_data),
        }

    def _mann_whitney_test(
        self, df: pd.DataFrame, test_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform Mann-Whitney U test."""
        column = test_spec.get("column")
        group_column = test_spec.get("group_column")
        groups = test_spec.get("groups", [])

        if len(groups) != 2:
            return {"error": "Need exactly 2 groups for Mann-Whitney test"}

        group1_data = df[df[group_column] == groups[0]][column].dropna()
        group2_data = df[df[group_column] == groups[1]][column].dropna()

        if len(group1_data) < 1 or len(group2_data) < 1:
            return {"error": "Insufficient data in groups"}

        stat, p = mannwhitneyu(group1_data, group2_data, alternative="two-sided")

        return {
            "test_type": "mann_whitney",
            "groups": groups,
            "group1_size": len(group1_data),
            "group2_size": len(group2_data),
            "statistic": float(stat),
            "p_value": float(p),
            "significant": p < self.alpha,
        }

    def _chi_square_test(
        self, df: pd.DataFrame, test_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform chi-square test of independence."""
        var1 = test_spec.get("variable1")
        var2 = test_spec.get("variable2")

        if var1 not in df.columns or var2 not in df.columns:
            return {"error": "Variables not found in data"}

        # Create contingency table
        contingency_table = pd.crosstab(df[var1], df[var2])

        stat, p, dof, expected = chi2_contingency(contingency_table)

        return {
            "test_type": "chi_square",
            "variables": [var1, var2],
            "statistic": float(stat),
            "p_value": float(p),
            "degrees_of_freedom": int(dof),
            "significant": p < self.alpha,
            "contingency_table": contingency_table.to_dict(),
            "expected_frequencies": pd.DataFrame(
                expected,
                index=contingency_table.index,
                columns=contingency_table.columns,
            ).to_dict(),
        }

    def _anova_test(
        self, df: pd.DataFrame, test_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform one-way ANOVA."""
        column = test_spec.get("column")
        group_column = test_spec.get("group_column")

        groups = df[group_column].unique()
        group_data = [
            df[df[group_column] == group][column].dropna() for group in groups
        ]

        # Filter out empty groups
        group_data = [data for data in group_data if len(data) > 0]

        if len(group_data) < 2:
            return {"error": "Need at least 2 groups for ANOVA"}

        stat, p = stats.f_oneway(*group_data)

        return {
            "test_type": "anova",
            "column": column,
            "group_column": group_column,
            "n_groups": len(group_data),
            "statistic": float(stat),
            "p_value": float(p),
            "significant": p < self.alpha,
        }

    def _kruskal_wallis_test(
        self, df: pd.DataFrame, test_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform Kruskal-Wallis test."""
        column = test_spec.get("column")
        group_column = test_spec.get("group_column")

        groups = df[group_column].unique()
        group_data = [
            df[df[group_column] == group][column].dropna() for group in groups
        ]

        # Filter out empty groups
        group_data = [data for data in group_data if len(data) > 0]

        if len(group_data) < 2:
            return {"error": "Need at least 2 groups for Kruskal-Wallis test"}

        stat, p = kruskal(*group_data)

        return {
            "test_type": "kruskal_wallis",
            "column": column,
            "group_column": group_column,
            "n_groups": len(group_data),
            "statistic": float(stat),
            "p_value": float(p),
            "significant": p < self.alpha,
        }

    def _analyze_trend(self, ts: pd.Series) -> Dict[str, Any]:
        """Analyze trend in time series."""
        # Linear trend
        x = np.arange(len(ts))
        y = ts.values

        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        return {
            "linear_trend": {
                "slope": float(slope),
                "intercept": float(intercept),
                "r_squared": float(r_value**2),
                "p_value": float(p_value),
                "significant": p_value < self.alpha,
                "direction": (
                    "increasing"
                    if slope > 0
                    else "decreasing"
                    if slope < 0
                    else "stable"
                ),
            },
            "percent_change": {
                "total": (
                    float((ts.iloc[-1] - ts.iloc[0]) / ts.iloc[0] * 100)
                    if ts.iloc[0] != 0
                    else 0
                ),
                "average_period": float(ts.pct_change().mean() * 100),
            },
        }

    def _analyze_autocorrelation(
        self, ts: pd.Series, max_lags: int = 10
    ) -> Dict[str, Any]:
        """Analyze autocorrelation in time series."""
        from statsmodels.tsa.stattools import acf, pacf

        try:
            # Calculate autocorrelation function
            autocorr = acf(ts, nlags=min(max_lags, len(ts) // 4), fft=False)

            # Calculate partial autocorrelation function
            partial_autocorr = pacf(ts, nlags=min(max_lags, len(ts) // 4))

            return {
                "autocorrelation": [float(x) for x in autocorr],
                "partial_autocorrelation": [float(x) for x in partial_autocorr],
                "significant_lags": [
                    i
                    for i, x in enumerate(autocorr)
                    if abs(x) > 2 / np.sqrt(len(ts)) and i > 0
                ],
            }
        except Exception as e:
            return {"error": str(e)}

    def _test_stationarity(self, ts: pd.Series) -> Dict[str, Any]:
        """Test stationarity of time series."""
        from statsmodels.tsa.stattools import adfuller

        try:
            result = adfuller(ts.dropna())

            return {
                "adf_test": {
                    "statistic": float(result[0]),
                    "p_value": float(result[1]),
                    "critical_values": {k: float(v) for k, v in result[4].items()},
                    "is_stationary": result[1] < self.alpha,
                }
            }
        except Exception as e:
            return {"error": str(e)}

    def _calculate_effect_size(
        self, group1: pd.Series, group2: pd.Series
    ) -> Dict[str, float]:
        """Calculate effect size measures."""
        mean1, mean2 = group1.mean(), group2.mean()
        std1, std2 = group1.std(), group2.std()
        n1, n2 = len(group1), len(group2)

        # Cohen's d
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        cohens_d = (mean1 - mean2) / pooled_std if pooled_std > 0 else 0

        return {
            "cohens_d": float(cohens_d),
            "mean_difference": float(mean1 - mean2),
            "standardized_mean_difference": float(cohens_d),
        }
