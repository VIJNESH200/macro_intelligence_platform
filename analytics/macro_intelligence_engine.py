import pandas as pd
import numpy as np

class MacroIntelligenceEngine:
    """The analytical core of the Macro Intelligence Platform.
    
    Evaluates standardized macro features to determine directional impact,
    computes an aggregate Macro Score, and detects structural regime shifts.
    """

    @staticmethod
    def evaluate_indicators(df: pd.DataFrame, idx: int) -> dict:
        """Evaluate the state of each macro driver at the given index using rolling Z-scores."""
        try:
            from ..config import MACRO_SERIES
        except ImportError:
            from config import MACRO_SERIES
        
        evaluations = {}
        for name in MACRO_SERIES.keys():
            if name in ['Yield 10Y', 'Yield Short']:
                continue
                
            z_col = f"{name}_Z"
            if z_col not in df.columns:
                continue
                
            z_val = df[z_col].iloc[idx]
            if pd.isna(z_val):
                evaluations[name] = {'score': 0.0, 'state': "Unknown", 'symbol': "►", 'momentum': 0.0}
                continue
                
            # CPI and Real Policy Rate are structurally inverse to growth (tighter/restrictive drags cycle down)
            multiplier = -1 if name in ['CPI', 'Real Policy Rate'] else 1
            impact_score = z_val * multiplier
            
            # Level Evaluation
            if impact_score > 0.5:
                level_state = "Positive"
                symbol = "▲"
            elif impact_score < -0.5:
                level_state = "Negative"
                symbol = "▼"
            else:
                level_state = "Neutral"
                symbol = "►"
                
            # Trend Evaluation
            mom_col = f"{name}_MoM"
            mom_val = df[mom_col].iloc[idx] if mom_col in df.columns else 0
            
            # Meaning of trend depends on the multiplier
            trend_impact = mom_val * multiplier
            # If the change is very small, call it Flat
            if abs(trend_impact) < 0.01:
                trend_state = "Flat"
            elif trend_impact > 0:
                trend_state = "Improving"
            else:
                trend_state = "Weakening"
                
            # Raw Value, YoY & Percentile
            raw_val = df[name].iloc[idx]
            
            yoy_val = np.nan
            base_col = f"{name}_Base"
            if base_col in df.columns:
                info = MACRO_SERIES.get(name)
                if info and info.transformation == 'yoy':
                    yoy_val = df[base_col].iloc[idx]
                elif info and info.transformation == 'real_rate':
                    raw_val = df[base_col].iloc[idx]
            else:
                # Fallback for tests or legacy
                if idx >= 12:
                    prev_12m = df[name].iloc[idx-12]
                    if not pd.isna(prev_12m) and prev_12m != 0 and not pd.isna(raw_val):
                        if raw_val == prev_12m and raw_val == df[name].iloc[idx-6]:
                            yoy_val = np.nan
                        elif name == 'Yield Spread':
                            yoy_val = (raw_val - prev_12m) * 100
                        else:
                            yoy_val = (raw_val - prev_12m) / abs(prev_12m) * 100
            
            # 10-year percentile (120 months)
            start_idx = max(0, idx - 120)
            base_col = f"{name}_Base"
            feature_col = base_col if base_col in df.columns else name
            window_data = df[feature_col].iloc[start_idx:idx+1].dropna()
            feat_val = df[feature_col].iloc[idx]
            if not window_data.empty and not pd.isna(feat_val):
                pct = (window_data < feat_val).mean() * 100
                pct_val = int(round(pct))
                if pct_val % 10 == 1 and pct_val % 100 != 11:
                    suffix = 'st'
                elif pct_val % 10 == 2 and pct_val % 100 != 12:
                    suffix = 'nd'
                elif pct_val % 10 == 3 and pct_val % 100 != 13:
                    suffix = 'rd'
                else:
                    suffix = 'th'
                percentile_str = f"{pct_val}{suffix} percentile"
            else:
                percentile_str = "N/A"
            
            evaluations[name] = {
                'score': impact_score,
                'state': level_state,  # backward compatibility
                'level': level_state,
                'trend': trend_state,
                'raw_value': raw_val,
                'yoy_value': yoy_val,
                'percentile': percentile_str,
                'symbol': symbol,
                'momentum': mom_val
            }
        return evaluations

    @staticmethod
    def assign_contribution(df: pd.DataFrame, idx: int) -> dict:
        """Calculate the overall Macro Score and rank the indicators."""
        evals = MacroIntelligenceEngine.evaluate_indicators(df, idx)
        
        drivers = []
        for name, data in evals.items():
            drivers.append({
                'indicator': name,
                'score': data['score'],
                'state': data['state'],
                'symbol': data['symbol']
            })
            
        # Sort by impact score (highest positive first)
        drivers.sort(key=lambda x: x['score'], reverse=True)
        
        try:
            from ..config import MACRO_SERIES
        except ImportError:
            from config import MACRO_SERIES
            
        total_expected_drivers = len([k for k in MACRO_SERIES.keys() if k not in ['Yield 10Y', 'Yield Short']])
        valid_drivers = [d for name, d in evals.items() if d['state'] != 'Unknown']
        missing_count = total_expected_drivers - len(valid_drivers)
        
        if len(valid_drivers) <= (total_expected_drivers / 2):
            total_score = None
            interp = "Neutral (Insufficient Data)"
            confidence = 0.0
            rationale = f"Available drivers: {len(valid_drivers)} of {total_expected_drivers}"
        else:
            total_score = sum(d['score'] for d in drivers if not pd.isna(d['score']))
            
            # Qualitative Interpretation
            if total_score > 2.0:
                interp = "Strongly Positive"
            elif total_score > 1.0:
                interp = "Positive"
            elif total_score > -1.0:
                interp = "Neutral"
            elif total_score > -2.0:
                interp = "Negative"
            else:
                interp = "Strongly Negative"
            
            avg_abs_z = sum(abs(d['score']) for d in valid_drivers) / len(valid_drivers)
            mag_score = min(1.0, avg_abs_z / 2.0)
            
            improving = sum(1 for d in valid_drivers if d['trend'] == 'Improving')
            weakening = sum(1 for d in valid_drivers if d['trend'] == 'Weakening')
            flat = sum(1 for d in valid_drivers if d['trend'] == 'Flat')
            max_trend = max(improving, weakening, flat)
            consist_score = max_trend / len(valid_drivers)
            
            recent_moms = [abs(d['momentum']) for d in valid_drivers if d['momentum'] != 0]
            if recent_moms:
                avg_mom = sum(recent_moms) / len(recent_moms)
                stab_score = max(0.0, 1.0 - (avg_mom / 1.5))
            else:
                stab_score = 1.0
                
            confidence = (mag_score * 40) + (consist_score * 40) + (stab_score * 20)
            
            penalty = (missing_count / total_expected_drivers) * 100
            confidence = max(0.0, confidence - penalty)
            
            rationale_parts = []
            if missing_count > 0:
                rationale_parts.append(f"Available drivers: {len(valid_drivers)} of {total_expected_drivers}")
            if consist_score < 0.5:
                rationale_parts.append("weak trend agreement")
            elif consist_score > 0.8:
                rationale_parts.append("strong trend agreement")
            if mag_score < 0.3:
                rationale_parts.append("weak signal strength")
            elif mag_score > 0.7:
                rationale_parts.append("strong signal magnitude")
                
            if rationale_parts:
                rationale = "; ".join(rationale_parts).capitalize() + "."
            else:
                rationale = "Robust signals across indicators."
        
        return {
            'all_drivers': drivers,
            'macro_score': total_score,
            'macro_interpretation': interp,
            'confidence_score': confidence,
            'confidence_rationale': rationale,
            'evaluations': evals
        }
        
    @staticmethod
    def generate_overall_stance(macro_score: float | None, avg_fwd: float | None) -> dict:
        """Single decision engine for generating Research View and Overall Stance."""
        if macro_score is None:
            return {
                "stance": "Neutral",
                "rationale": "Insufficient data to compute macro score."
            }
            
        avg_fwd = avg_fwd if avg_fwd is not None and not pd.isna(avg_fwd) else 0.0
        
        if macro_score >= 1.5 and avg_fwd >= 0:
            stance = "Highly Constructive"
            rationale = f"Macro Score {macro_score:+.2f} | Favorable Historical Precedents"
        elif macro_score >= 0.5:
            stance = "Constructive"
            rationale = f"Macro Score {macro_score:+.2f} | Positive Growth Vector"
        elif macro_score < -1.5 and avg_fwd < -2:
            stance = "Highly Defensive"
            rationale = f"Macro Score {macro_score:+.2f} | Negative Historical Precedents"
        elif macro_score < -0.5:
            stance = "Defensive"
            rationale = f"Macro Score {macro_score:+.2f} | Deteriorating Fundamentals"
        else:
            stance = "Cautious"
            rationale = f"Macro Score {macro_score:+.2f} | Mixed Signals"
            
        return {
            "stance": stance,
            "rationale": rationale
        }

    @staticmethod
    def detect_regime_shifts(df: pd.DataFrame, idx: int) -> list[str]:
        """Detect structural regime shifts in the macroeconomic landscape."""
        shifts = []
        if idx < 1:
            return shifts
            
        # 1. PMI (Manufacturing)
        if 'PMI' in df.columns:
            prev_pmi = df['PMI'].iloc[idx-1]
            curr_pmi = df['PMI'].iloc[idx]
            if prev_pmi >= 50 > curr_pmi:
                shifts.append("⚠ Manufacturing entered contraction")
            elif prev_pmi < 50 <= curr_pmi:
                shifts.append("↑ Manufacturing entered expansion")
                
        # 2. CPI (Inflation)
        if 'CPI_Z' in df.columns:
            prev_cpi = df['CPI_Z'].iloc[idx-1]
            curr_cpi = df['CPI_Z'].iloc[idx]
            if prev_cpi > 1.0 and curr_cpi < 0.0:
                shifts.append("↓ Inflation falling rapidly")
            elif prev_cpi < 0.0 and curr_cpi > 1.0:
                shifts.append("↑ Inflation rising rapidly")
                
        # 3. Real Policy Rate
        if 'Real Policy Rate_Z' in df.columns:
            prev_rpr = df['Real Policy Rate_Z'].iloc[idx-1]
            curr_rpr = df['Real Policy Rate_Z'].iloc[idx]
            if prev_rpr < 0.0 and curr_rpr > 1.0:
                shifts.append("↑ Real policy rate tightening (restrictive)")
            elif prev_rpr > 1.0 and curr_rpr < 0.0:
                shifts.append("↓ Real policy rate easing (accommodative)")
                
        # 4. Yield Curve
        if 'Yield Spread' in df.columns:
            prev_spread = df['Yield Spread'].iloc[idx-1]
            curr_spread = df['Yield Spread'].iloc[idx]
            if prev_spread > 0 >= curr_spread:
                shifts.append("⚠ Yield curve inverted (Recession signal)")
            elif prev_spread < 0 <= curr_spread:
                shifts.append("↑ Yield curve un-inverted (Steepening)")
            elif prev_spread > 1.5 and curr_spread < 0.5:
                shifts.append("→ Yield curve flattening")
                
        return shifts
