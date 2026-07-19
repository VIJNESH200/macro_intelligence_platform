"""
Forecasting Engine — Projects business cycle trajectory forward.
================================================================
Uses a three-signal consensus (Momentum Extrapolation, Historical
Analogue Consensus, Macro Driver Forward Signal) to project X/Y
coordinates for 3-month and 6-month horizons with confidence bands.
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
        forecasts = {}
        projected_path = [(x_now, y_now)]
        
        for h in range(1, max(horizons) + 1):
            x_blend = (
                weights['momentum'] * mom_proj['path'][h - 1][0] +
                weights['analogues'] * ana_proj['path'][h - 1][0] +
                weights['macro_drivers'] * macro_proj['path'][h - 1][0]
            )
            y_blend = (
                weights['momentum'] * mom_proj['path'][h - 1][1] +
                weights['analogues'] * ana_proj['path'][h - 1][1] +
                weights['macro_drivers'] * macro_proj['path'][h - 1][1]
            )
            projected_path.append((x_blend, y_blend))

            if h in horizons:
                quadrant = ForecastingEngine._get_quadrant(x_blend, y_blend, center)
                conv = ForecastingEngine._compute_conviction(
                    macro_contrib, analogues, h
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
                if len(matching_indices) > 0:
                    ana_idx = matching_indices[0]
                    future_idx = ana_idx + h
                    if future_idx <= idx:
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
        """Signal 3: Directional bias from macro driver trends."""
        x_now = df['X'].iloc[idx]
        y_now = df['Y'].iloc[idx]

        if not macro_contrib or not macro_contrib.get('evaluations'):
            return {'path': [(x_now, y_now)] * max_h}

        evals = macro_contrib['evaluations']
        
        # Count improving vs weakening
        improving = 0
        weakening = 0
        for name, ev in evals.items():
            trend = ev.get('trend', 'Flat')
            if trend == 'Improving':
                improving += 1
            elif trend == 'Weakening':
                weakening += 1

        total = improving + weakening
        if total == 0:
            net_direction = 0.0
        else:
            net_direction = (improving - weakening) / total  # -1 to +1

        # Scale by macro score magnitude
        macro_score = macro_contrib.get('macro_score', 0) or 0
        magnitude = min(abs(macro_score) / 3.0, 1.0)  # Normalize to 0-1

        # Directional shift per month
        dx_per_month = net_direction * magnitude * 0.3  # scaled to reasonable units
        dy_per_month = net_direction * magnitude * 0.2  # momentum shifts more slowly

        path = []
        x_proj, y_proj = x_now, y_now
        for h in range(1, max_h + 1):
            x_proj += dx_per_month
            y_proj += dy_per_month
            path.append((x_proj, y_proj))

        return {'path': path}

    @staticmethod
    def _compute_conviction(macro_contrib, analogues, horizon):
        """Compute Forecast Conviction score (0-100%)."""
        # Start from a high baseline conviction
        conviction = 90.0

        # 1. Penalize for trend disagreement (consistency)
        if macro_contrib and macro_contrib.get('evaluations'):
            evals = macro_contrib['evaluations']
            trends = [ev.get('trend', 'Flat') for ev in evals.values() if ev.get('state') != 'Unknown']
            if trends:
                improving = trends.count('Improving')
                weakening = trends.count('Weakening')
                flat = trends.count('Flat')
                consistency = max(improving, weakening, flat) / len(trends)
                # Max penalty of 20% for complete disagreement
                conviction -= (1.0 - consistency) * 20.0

        # 2. Penalize for analogue outcomes dispersion
        if analogues and analogues.get('matches'):
            matches = [m for m in analogues['matches'] if m.get('similarity_score') is not None]
            if matches:
                sims = [m['similarity_score'] for m in matches]
                avg_sim = sum(sims) / len(sims)
                # Low similarity penalizes conviction
                conviction -= (100.0 - avg_sim) * 0.5

        # 3. Penalize for missing data
        if macro_contrib and 'all_drivers' in macro_contrib:
            unknowns = sum(1 for d in macro_contrib['all_drivers'] if d.get('state') == 'Unknown')
            conviction -= unknowns * 10.0

        # 4. Decay over the horizon (5% per month)
        conviction -= (horizon - 1) * 5.0

        return max(10.0, min(95.0, conviction))

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
