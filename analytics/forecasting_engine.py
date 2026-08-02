from __future__ import annotations
"""
Forecasting Engine — Projects business cycle trajectory forward.
================================================================
Blends three signals — CLI Momentum, Historical Analogues, and Macro Drivers —
to project X/Y coordinates for 3-month and 6-month horizons. Weights come from
the active market profile (config.markets); both markets currently use
40% / 35% / 25%. Weights are re-normalized across whichever signals produced a
real projection, but in practice all three do (analogues fall back on ~3-5% of
steps, the others effectively never), so the live blend is the full 40/35/25.

Empirical Backtest Note (India, full sample 2007-2026):
- Momentum 67.7%, Analogues 63.3%, Macro Drivers 65.9%; blended 71.2%.
- Held-out (2019-2026) blended accuracy is 68.2%.
- The same blend on US scores 56.3% full-sample / 51.8% held-out. The signal
  ranking inverts there (Momentum is India's strongest and the US's weakest),
  but per-market re-fitting failed held-out evaluation -- see config.markets.
"""
import numpy as np
import pandas as pd


class ForecastingEngine:
    """Projects future X (Health) and Y (Momentum) coordinates."""

    @staticmethod
    def project(df: pd.DataFrame, idx: int, config: dict,
                analogues: dict, macro_contrib: dict) -> dict:
        """Main entry point — compute forward projections.

        Args:
            df: Full DataFrame with X, Y, Velocity, Quadrant, and macro Z-score columns.
            idx: Current observation index.
            config: Main CONFIG dict (with 'center', 'window', etc.)
            analogues: Output from historical_analogues.generate_analogues()
            macro_contrib: Output from MacroIntelligenceEngine.assign_contribution()

        Returns:
            Dict with forecast_3m, forecast_6m, projected_path, confidence_band,
            method_contributions, and residual_std.
        """
        try:
            from ..config import FORECAST_CONFIG
        except ImportError:
            from config import FORECAST_CONFIG

        center = config.get('center', 100)
        horizons = FORECAST_CONFIG['horizons']
        weights = FORECAST_CONFIG['weights']
        decay = FORECAST_CONFIG['decay_factor']
        conf_decay = FORECAST_CONFIG['confidence_decay_per_month']

        x_now = df['X'].iloc[idx]
        y_now = df['Y'].iloc[idx]

        # ---- Signal 1: Momentum Extrapolation (40%) ----
        mom_proj = ForecastingEngine._momentum_signal(df, idx, center, decay, max(horizons))

        # ---- Signal 2: Historical Analogue Consensus (35%) ----
        ana_proj = ForecastingEngine._analogue_signal(df, idx, analogues, max(horizons))

        # ---- Signal 3: Macro Driver Forward Signal (25%) ----
        macro_proj = ForecastingEngine._macro_driver_signal(
            df, idx, center, macro_contrib, max(horizons)
        )

        # ---- Blend signals for each horizon ----
        # Track which signals produced real projections vs. static fallbacks.
        # Re-normalize weights among active signals to avoid dead-weight dampening.
        w = dict(weights)  # copy
        active_signals = {
            'momentum': mom_proj,
            'analogues': ana_proj,
            'macro_drivers': macro_proj
        }

        # Detect fallback signals (all points identical to current position)
        fallback_keys = []
        for key, sig in active_signals.items():
            path = sig['path']
            if all(abs(p[0] - x_now) < 1e-6 and abs(p[1] - y_now) < 1e-6 for p in path):
                fallback_keys.append(key)

        # Re-normalize weights if some signals fell back
        if fallback_keys and len(fallback_keys) < len(active_signals):
            active_weight_sum = sum(w[k] for k in w if k not in fallback_keys)
            if active_weight_sum > 0:
                for k in fallback_keys:
                    w[k] = 0.0
                for k in w:
                    if k not in fallback_keys:
                        w[k] = w[k] / active_weight_sum

        forecasts = {}
        projected_path = [(x_now, y_now)]
        
        for h in range(1, max(horizons) + 1):
            x_blend = (
                w['momentum'] * mom_proj['path'][h - 1][0] +
                w['analogues'] * ana_proj['path'][h - 1][0] +
                w['macro_drivers'] * macro_proj['path'][h - 1][0]
            )
            y_blend = (
                w['momentum'] * mom_proj['path'][h - 1][1] +
                w['analogues'] * ana_proj['path'][h - 1][1] +
                w['macro_drivers'] * macro_proj['path'][h - 1][1]
            )
            projected_path.append((x_blend, y_blend))

            if h in horizons:
                quadrant = ForecastingEngine._get_quadrant(x_blend, y_blend, center)
                conv = ForecastingEngine._compute_conviction(
                    mom_proj['path'][h - 1],
                    ana_proj['path'][h - 1],
                    macro_proj['path'][h - 1],
                    center,
                    analogues,
                    macro_contrib,
                    h,
                    weights=w,
                    conf_decay=conf_decay
                )
                forecasts[f'forecast_{h}m'] = {
                    'x': round(x_blend, 4),
                    'y': round(y_blend, 4),
                    'quadrant': quadrant,
                    'conviction': round(conv, 1)
                }

        # ---- Confidence bands ----
        residual_std = ForecastingEngine._estimate_residual_std(df, idx)
        confidence_band = ForecastingEngine._compute_confidence_bands(
            projected_path, residual_std
        )

        # ---- Method contributions (for transparency) ----
        max_h = max(horizons)
        method_contributions = {
            'momentum': {
                'x': round(mom_proj['path'][max_h - 1][0], 4),
                'y': round(mom_proj['path'][max_h - 1][1], 4)
            },
            'analogues': {
                'x': round(ana_proj['path'][max_h - 1][0], 4),
                'y': round(ana_proj['path'][max_h - 1][1], 4)
            },
            'macro_drivers': {
                'x': round(macro_proj['path'][max_h - 1][0], 4),
                'y': round(macro_proj['path'][max_h - 1][1], 4)
            }
        }

        result = {
            'projected_path': projected_path,
            'confidence_band': confidence_band,
            'method_contributions': method_contributions,
            'residual_std': residual_std
        }
        result.update(forecasts)
        return result

    @staticmethod
    def _momentum_signal(df, idx, center, decay, max_h):
        """Signal 1: Extrapolate recent velocity with exponential decay toward center."""
        x_now = df['X'].iloc[idx]
        y_now = df['Y'].iloc[idx]

        # Use trailing 3-month velocity vector
        lookback = min(3, idx)
        if lookback > 0:
            dx_per_month = (df['X'].iloc[idx] - df['X'].iloc[idx - lookback]) / lookback
            dy_per_month = (df['Y'].iloc[idx] - df['Y'].iloc[idx - lookback]) / lookback
        else:
            dx_per_month = 0.0
            dy_per_month = 0.0

        path = []
        x_proj, y_proj = x_now, y_now
        for h in range(1, max_h + 1):
            decay_h = decay ** h
            x_proj = x_proj + dx_per_month * decay_h
            y_proj = y_proj + dy_per_month * decay_h
            # Gentle mean-reversion pull toward center
            x_proj = x_proj + (center - x_proj) * (1 - decay_h) * 0.1
            y_proj = y_proj + (center - y_proj) * (1 - decay_h) * 0.1
            path.append((x_proj, y_proj))

        return {'path': path}

    @staticmethod
    def _analogue_signal(df, idx, analogues, max_h):
        """Signal 2: Similarity-weighted average of where analogues went next."""
        x_now = df['X'].iloc[idx]
        y_now = df['Y'].iloc[idx]

        if not analogues or not analogues.get('matches'):
            # Fallback: assume staying at current position
            return {'path': [(x_now, y_now)] * max_h}

        matches = analogues['matches']
        path = []

        for h in range(1, max_h + 1):
            weighted_x = 0.0
            weighted_y = 0.0
            total_weight = 0.0

            for m in matches:
                sim = m['similarity_score'] / 100.0
                # Find the analogue's date index in df
                analogue_date = pd.Timestamp(m['date_str'])
                # Find the closest index matching this date
                matching_indices = df.index.get_indexer([analogue_date], method='nearest')
                if len(matching_indices) > 0 and matching_indices[0] >= 0:
                    ana_idx = matching_indices[0]
                    future_idx = ana_idx + h
                    if 0 <= future_idx <= idx:
                        weighted_x += sim * df['X'].iloc[future_idx]
                        weighted_y += sim * df['Y'].iloc[future_idx]
                        total_weight += sim

            if total_weight > 0:
                path.append((weighted_x / total_weight, weighted_y / total_weight))
            else:
                path.append((x_now, y_now))

        return {'path': path}

    @staticmethod
    def _macro_driver_signal(df, idx, center, macro_contrib, max_h):
        """Signal 3: Walk-forward fitted Ridge regression projection on macro driver Z-scores."""
        x_now = df['X'].iloc[idx]
        y_now = df['Y'].iloc[idx]

        feature_cols = ['X', 'Y']
        for col in df.columns:
            if col.endswith('_Z'):
                feature_cols.append(col)

        # Require historical lookback for training (strictly prior to forecast)
        train_end = idx - 6
        if train_end + 1 < 36:
            return {'path': [(x_now, y_now)] * max_h}

        try:
            train_df = df.iloc[:train_end + 1]
            if len(train_df) < 36:
                return {'path': [(x_now, y_now)] * max_h}

            df_feats = df[feature_cols].fillna(0.0).to_numpy()
            N = train_end - 5  # training sample count (strictly prior to idx)
            if N < 30:
                return {'path': [(x_now, y_now)] * max_h}

            X_train = df_feats[:N]
            y_dx = df['X'].iloc[6:train_end + 1].to_numpy() - df['X'].iloc[:N].to_numpy()
            y_dy = df['Y'].iloc[6:train_end + 1].to_numpy() - df['Y'].iloc[:N].to_numpy()

            # Centered L2 Ridge solve (alpha=10.0 for strong regularization)
            X_mean = X_train.mean(axis=0)
            X_centered = X_train - X_mean
            y_dx_mean = float(y_dx.mean())
            y_dy_mean = float(y_dy.mean())

            y_dx_centered = y_dx - y_dx_mean
            y_dy_centered = y_dy - y_dy_mean

            XtX = X_centered.T @ X_centered + 10.0 * np.eye(X_train.shape[1])
            w_dx = np.linalg.solve(XtX, X_centered.T @ y_dx_centered)
            w_dy = np.linalg.solve(XtX, X_centered.T @ y_dy_centered)

            curr_feat = df_feats[idx]
            curr_centered = curr_feat - X_mean

            pred_dx_6m = float(curr_centered @ w_dx + y_dx_mean)
            pred_dy_6m = float(curr_centered @ w_dy + y_dy_mean)

            # Construct mean-reverting path scaling up to 6M prediction
            decay = 0.85
            scale_6m = (1.0 - (decay ** 6))

            path = []
            for h in range(1, max_h + 1):
                scale = (1.0 - (decay ** h)) / scale_6m if scale_6m > 0 else (h / 6.0)
                path.append((x_now + pred_dx_6m * scale, y_now + pred_dy_6m * scale))

            return {'path': path}
        except Exception as e:
            print(f"  [!] Notice: Macro driver Ridge model fallback ({e}); using persistence path.")
            return {'path': [(x_now, y_now)] * max_h}

    @staticmethod
    def _compute_conviction(mom_pt, ana_pt, macro_pt, center, analogues, macro_contrib, horizon,
                           weights=None, conf_decay=0.15):
        """Compute Forecast Conviction score (0-100%) based on active non-zero weighted signal consensus agreement."""
        signal_quads = {
            'momentum': ForecastingEngine._get_quadrant(mom_pt[0], mom_pt[1], center),
            'analogues': ForecastingEngine._get_quadrant(ana_pt[0], ana_pt[1], center),
            'macro_drivers': ForecastingEngine._get_quadrant(macro_pt[0], macro_pt[1], center)
        }

        # Filter active signals with non-zero weight
        if weights:
            active_keys = [k for k, v in weights.items() if v > 0.0 and k in signal_quads]
        else:
            active_keys = ['momentum', 'analogues', 'macro_drivers']

        if not active_keys:
            active_keys = ['momentum', 'analogues']

        active_quads = [signal_quads[k] for k in active_keys]
        from collections import Counter
        most_common_count = Counter(active_quads).most_common(1)[0][1]
        n_active = len(active_keys)

        if n_active >= 3:
            if most_common_count == 3:
                base_conv = 72.0  # Unanimous 3-signal agreement
            elif most_common_count == 2:
                base_conv = 54.0  # Majority 2/3 agreement
            else:
                base_conv = 32.0  # Split 3-signal consensus
        elif n_active == 2:
            if most_common_count == 2:
                base_conv = 72.0  # Unanimous 2-signal agreement
            else:
                base_conv = 42.0  # Split 2-signal consensus
        else:
            # Single active signal
            base_conv = 65.0

        # Adjust for analogue similarity quality
        if analogues and analogues.get('matches'):
            matches = [m for m in analogues['matches'] if m.get('similarity_score') is not None]
            if matches:
                sims = [m['similarity_score'] for m in matches]
                avg_sim = sum(sims) / len(sims)
                base_conv += (avg_sim - 70.0) * 0.25

        # Apply horizon uncertainty decay configured by conf_decay (0.15 -> 3.0 pts/month)
        monthly_decay_pts = conf_decay * 20.0
        base_conv -= (horizon - 1) * monthly_decay_pts

        return max(15.0, min(95.0, base_conv))

    @staticmethod
    def _estimate_residual_std(df, idx):
        """Estimate the standard deviation of month-over-month X/Y changes."""
        lookback = min(36, idx)
        if lookback < 2:
            return {'x': 1.0, 'y': 1.0}

        x_changes = df['X'].iloc[idx - lookback:idx].diff().dropna()
        y_changes = df['Y'].iloc[idx - lookback:idx].diff().dropna()

        return {
            'x': float(x_changes.std()) if len(x_changes) > 0 else 1.0,
            'y': float(y_changes.std()) if len(y_changes) > 0 else 1.0
        }

    @staticmethod
    def _compute_confidence_bands(projected_path, residual_std):
        """Compute 50th and 80th percentile confidence ellipses around path."""
        inner = []  # 50th percentile (±0.67σ)
        outer = []  # 80th percentile (±1.28σ)

        for i, (x, y) in enumerate(projected_path):
            # Uncertainty grows with sqrt(horizon)
            scale = np.sqrt(max(1, i))
            sx = residual_std['x'] * scale
            sy = residual_std['y'] * scale

            inner.append({
                'x': x, 'y': y,
                'dx': 0.67 * sx, 'dy': 0.67 * sy
            })
            outer.append({
                'x': x, 'y': y,
                'dx': 1.28 * sx, 'dy': 1.28 * sy
            })

        return {'inner': inner, 'outer': outer}

    @staticmethod
    def _get_quadrant(x, y, center):
        if x >= center and y >= center:
            return 'Expansion'
        elif x >= center and y < center:
            return 'Slowdown'
        elif x < center and y < center:
            return 'Contraction'
        else:
            return 'Recovery'
