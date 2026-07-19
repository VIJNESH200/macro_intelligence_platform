"""
Scenario Engine — Bull, Base, Bear scenario analysis.
=====================================================
Generates probabilistic paths based on the base forecast,
transition matrix probabilities, and historical analogue bounds.
"""
import numpy as np


class ScenarioEngine:
    """Generates Bull, Base, Bear scenarios with associated probabilities and returns."""

    @staticmethod
    def generate_scenarios(forecast_result: dict, transition_result: dict,
                           analogues: dict, current_quadrant: str, config: dict) -> list:
        """
        Generate three scenarios.
        
        Args:
            forecast_result: Output of ForecastingEngine.project()
            transition_result: Output of transition_matrix.compute_transition_matrix()
            analogues: Output of historical_analogues.generate_analogues()
            current_quadrant: The current business cycle quadrant (e.g. 'Expansion')
            config: Main app CONFIG
            
        Returns:
            list of dicts, one for each scenario (Bull, Base, Bear)
        """
        try:
            from ..config import FORECAST_CONFIG
        except ImportError:
            from config import FORECAST_CONFIG

        center = config.get('center', 100)
        sigma = FORECAST_CONFIG.get('scenario_sigma', 1.0)
        
        # 1. Probabilities from transition matrix and macro drivers
        skew = 0.0
        if transition_result and current_quadrant in transition_result.get('labels', []):
            try:
                from ..analytics.transition_matrix import get_transition_probs_from
            except ImportError:
                from analytics.transition_matrix import get_transition_probs_from
                
            raw_probs = get_transition_probs_from(transition_result['matrix'], current_quadrant)
            
            # Transition probability of staying in or moving to positive quadrants (Expansion, Recovery)
            pos_prob = raw_probs.get('Expansion', 0) + raw_probs.get('Recovery', 0)
            neg_prob = raw_probs.get('Contraction', 0) + raw_probs.get('Slowdown', 0)
            
            if (pos_prob + neg_prob) > 0:
                # transition skew bounds between -0.3 and +0.3
                skew += (pos_prob - neg_prob) / (pos_prob + neg_prob) * 0.3
                
        # Skew from Macro Score
        macro_score = 0.0
        if forecast_result:
            if 'macro_score' in forecast_result:
                macro_score = forecast_result['macro_score']
            elif 'macro_contrib' in forecast_result:
                macro_score = forecast_result['macro_contrib'].get('macro_score', 0.0)
            elif isinstance(forecast_result, dict):
                # Fallback check on data input
                pass
                
        # Limit macro_score to range [-3.0, 3.0] for skew calculation
        norm_score = max(-3.0, min(3.0, macro_score))
        skew += (norm_score / 3.0) * 0.2  # macro skew bounds between -0.2 and +0.2
        
        # Limit total skew to [-0.4, 0.4]
        skew = max(-0.4, min(0.4, skew))
        
        probs = {
            'Base': 50.0,
            'Bull': 25.0 + (skew * 25.0),
            'Bear': 25.0 - (skew * 25.0)
        }

        # 2. Historical Returns Bounds
        fwd_returns = []
        if analogues and analogues.get('matches'):
            for m in analogues['matches']:
                val = m.get('fwd_ret_val')
                if val is not None and not np.isnan(val):
                    fwd_returns.append(val)
                    
        if fwd_returns:
            bull_ret = np.percentile(fwd_returns, 80)  # 80th percentile
            base_ret = np.mean(fwd_returns)
            bear_ret = np.percentile(fwd_returns, 20)  # 20th percentile
        else:
            bull_ret = np.nan
            base_ret = np.nan
            bear_ret = np.nan

        # 3. Path Generation
        base_path = forecast_result.get('projected_path', [])
        residual_std = forecast_result.get('residual_std', {'x': 1.0, 'y': 1.0})
        
        bull_path = []
        bear_path = []
        
        for i, (x, y) in enumerate(base_path):
            scale = np.sqrt(max(1, i))
            # Bull path: Higher Health (X), Better Momentum (Y)
            bull_path.append((
                x + (sigma * residual_std['x'] * scale),
                y + (0.5 * sigma * residual_std['y'] * scale)
            ))
            # Bear path: Lower Health (X), Worse Momentum (Y)
            bear_path.append((
                x - (sigma * residual_std['x'] * scale),
                y - (0.5 * sigma * residual_std['y'] * scale)
            ))

        # 4. Generate structured output
        horizons = FORECAST_CONFIG['horizons']
        h_idx_3m = min(3, len(base_path) - 1)
        h_idx_6m = min(6, len(base_path) - 1)
        
        scenarios = []
        
        # Helper to get quadrant safely
        def _q(path, idx):
            if not path or idx >= len(path): return "N/A"
            x, y = path[idx]
            if x >= center and y >= center: return 'Expansion'
            elif x >= center and y < center: return 'Slowdown'
            elif x < center and y < center: return 'Contraction'
            else: return 'Recovery'
            
        scenarios.append({
            'name': 'Bull',
            'probability': probs['Bull'],
            'projected_quadrant_3m': _q(bull_path, h_idx_3m),
            'projected_quadrant_6m': _q(bull_path, h_idx_6m),
            'expected_market_return_6m': bull_ret,
            'path': bull_path,
            'key_assumption': "Macro momentum accelerates faster than base expectations, driven by positive surprises in leading indicators.",
            'trigger': "Upside breakout in PMI or rapid yield curve steepening."
        })
        
        scenarios.append({
            'name': 'Base',
            'probability': probs['Base'],
            'projected_quadrant_3m': _q(base_path, h_idx_3m),
            'projected_quadrant_6m': _q(base_path, h_idx_6m),
            'expected_market_return_6m': base_ret,
            'path': base_path,
            'key_assumption': "Current cyclical trajectory persists with standard mean-reversion as projected by the three-signal consensus.",
            'trigger': "Continuation of current trend."
        })
        
        scenarios.append({
            'name': 'Bear',
            'probability': probs['Bear'],
            'projected_quadrant_3m': _q(bear_path, h_idx_3m),
            'projected_quadrant_6m': _q(bear_path, h_idx_6m),
            'expected_market_return_6m': bear_ret,
            'path': bear_path,
            'key_assumption': "Macroeconomic health deteriorates significantly as underlying fundamentals crack.",
            'trigger': "Systemic credit event, sharp CPI spike, or sustained PMI contraction."
        })

        return scenarios
