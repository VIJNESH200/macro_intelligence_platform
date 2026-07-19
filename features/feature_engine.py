"""
Feature Engine — Standardized feature computation for macro indicators.
=======================================================================
Converts raw indicator series into normalized features (Z-scores),
assigns business cycle quadrants, and computes smooth spline trails.
Exact behavioral port of calculate_metrics() from business_cycle_tracer.py.
"""
import numpy as np
import pandas as pd
import scipy.interpolate as interp


class FeatureEngine:
    """Computes derived features from raw macro indicator data."""

    @staticmethod
    def compute_health(series: pd.Series, window: int, center: float) -> pd.Series:
        """Economic Health — rolling Z-score of the raw indicator.

        X = center + (value - rolling_mean) / rolling_std
        """
        rolling_mean = series.rolling(window=window, min_periods=window).mean()
        rolling_std = series.rolling(window=window, min_periods=window).std(ddof=0)
        return center + (series - rolling_mean) / rolling_std

    @staticmethod
    def compute_momentum(series: pd.Series, window: int, center: float) -> pd.Series:
        """Economic Momentum — rolling Z-score of the 1-month change.

        Y = center + (diff - rolling_mean_diff) / rolling_std_diff
        """
        diff = series.diff(1)
        rolling_mean = diff.rolling(window=window, min_periods=window).mean()
        rolling_std = diff.rolling(window=window, min_periods=window).std(ddof=0)
        return center + (diff - rolling_mean) / rolling_std

    @staticmethod
    def compute_velocity(series: pd.Series, window: int, center: float) -> pd.Series:
        """Economic Velocity — rolling Z-score of the second derivative.

        Measures acceleration/deceleration of the underlying indicator.
        New in v2.0.
        """
        second_diff = series.diff(1).diff(1)
        rolling_mean = second_diff.rolling(window=window, min_periods=window).mean()
        rolling_std = second_diff.rolling(window=window, min_periods=window).std(ddof=0)
        # Avoid division by zero
        rolling_std = rolling_std.replace(0, np.nan)
        return center + (second_diff - rolling_mean) / rolling_std

    @staticmethod
    def assign_quadrants(x: pd.Series, y: pd.Series, center: float) -> pd.Series:
        """Assign business cycle quadrant based on Health (X) and Momentum (Y).

        Expansion:   X >= center AND Y >= center
        Slowdown:    X >= center AND Y <  center
        Contraction: X <  center AND Y <  center
        Recovery:    X <  center AND Y >= center
        """
        conditions = [
            (x >= center) & (y >= center),
            (x >= center) & (y < center),
            (x < center) & (y < center),
        ]
        choices = ['Expansion', 'Slowdown', 'Contraction']
        return pd.Series(
            np.select(conditions, choices, default='Recovery'),
            index=x.index
        )

    @staticmethod
    def compute_spline(df: pd.DataFrame, config: dict) -> pd.DataFrame:
        """Compute cubic B-spline interpolation for smooth trail rendering.

        Returns a DataFrame with columns: t, X, Y
        """
        x_all = df['X'].values
        y_all = df['Y'].values
        t_all = np.arange(len(x_all))

        if len(x_all) >= 4:
            spl_x = interp.make_interp_spline(t_all, x_all, k=3)
            spl_y = interp.make_interp_spline(t_all, y_all, k=3)

            pts_per_seg = config['points_per_segment']
            total_smooth_points = (len(x_all) - 1) * pts_per_seg + 1
            t_smooth = np.linspace(0, len(x_all) - 1, total_smooth_points)
            x_smooth = spl_x(t_smooth)
            y_smooth = spl_y(t_smooth)

            return pd.DataFrame({'t': t_smooth, 'X': x_smooth, 'Y': y_smooth})
        else:
            return pd.DataFrame({'t': t_all, 'X': x_all, 'Y': y_all})

    @classmethod
    def compute_macro_features(cls, df: pd.DataFrame, window: int) -> pd.DataFrame:
        """Compute standardized rolling Z-scores for all Macro Drivers using a generic pipeline."""
        try:
            from ..config import MACRO_SERIES
        except ImportError:
            from config import MACRO_SERIES

        # Pre-compute derived indicators if necessary
        if 'Yield 10Y' in df.columns and 'Yield Short' in df.columns:
            df['Yield Spread'] = df['Yield 10Y'] - df['Yield Short']

        for name, info in MACRO_SERIES.items():
            if name not in df.columns or name in ['Yield 10Y', 'Yield Short']:
                continue

            # 1. Clean
            series = df[name].copy()

            # 2. Normalize based on transformation type
            if info.transformation == 'yoy':
                base_feature = series.dropna().pct_change(12) * 100
            elif info.transformation == 'real_rate':
                # Repo rate level - CPI YoY rate
                cpi_yoy = df['CPI_Base'] if 'CPI_Base' in df.columns else (df['CPI'].pct_change(12)*100)
                repo_rate = series.reindex(df.index).ffill()
                base_feature = repo_rate - cpi_yoy
            elif info.transformation == 'spread':
                base_feature = series.dropna()
            else:  # level
                base_feature = series.dropna()

            # Align back to main index and forward fill the feature so Z-score calculation is stable
            base_feature = base_feature.reindex(df.index).ffill()
            df[f"{name}_Base"] = base_feature

            # 3. Features: Compute Rolling Z-score
            rolling_mean = base_feature.rolling(window=window, min_periods=window).mean()
            rolling_std = base_feature.rolling(window=window, min_periods=window).std(ddof=0)
            rolling_std = rolling_std.replace(0, np.nan)

            df[f"{name}_Z"] = (base_feature - rolling_mean) / rolling_std
            
            # Also calculate 1-month momentum of the base feature for simple momentum checks
            if info.transformation == 'yoy':
                df[f"{name}_MoM"] = base_feature.diff(1)
            else:
                df[f"{name}_MoM"] = base_feature.diff(1)

        return df

    @classmethod
    def compute_all(cls, df: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Main entry point — replicates calculate_metrics() exactly.

        Adds X, Y, Velocity, PMI, Quadrant columns to df.
        Returns (df, spline_data).
        """
        print("Calculating macro metrics...")

        ticker = config['ticker']
        window = config['window']
        center = config['center']
        cli = df[ticker]

        df['X'] = cls.compute_health(cli, window, center)
        df['Y'] = cls.compute_momentum(cli, window, center)
        df['Velocity'] = cls.compute_velocity(cli, window, center)
        # To avoid overwriting our new 'PMI' series, we rename the old reference
        df['CLI_Raw'] = cli

        df = cls.compute_macro_features(df, window)

        df = df.dropna(subset=['X', 'Y']).copy()
        df['Quadrant'] = cls.assign_quadrants(df['X'], df['Y'], center)
        
        # Ensure all columns (including market context) are forward-filled for the UI and intelligence engine
        df = df.ffill()

        spline_data = cls.compute_spline(df, config)
        return df, spline_data
