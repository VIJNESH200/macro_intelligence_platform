import pandas as pd
from .macro_intelligence_engine import MacroIntelligenceEngine

class ResearchEngine:
    """Deterministic Narrative Generation Engine for Macro Intelligence.
    
    Translates quantitative states (Level, Trend, Percentiles) into 
    structured institutional research insights.
    """

    @staticmethod
    def generate_insights(df: pd.DataFrame, idx: int) -> list[dict]:
        """Generate synthesized structured macro narratives based on current indicators.
        
        Returns a list of dictionaries with keys:
        - observation
        - evidence
        - interpretation
        - implication
        """
        evals = MacroIntelligenceEngine.evaluate_indicators(df, idx)
        
        insights = []
        
        # 1. Manufacturing (PMI)
        if 'PMI' in evals and evals['PMI']['state'] != 'Unknown':
            pmi = evals['PMI']
            insights.append({
                "observation": f"Manufacturing Index is at {pmi['raw_value']:.1f}, placing it in the {pmi['percentile']}.",
                "evidence": f"Z-score = {pmi['score']:+.2f}",
                "interpretation": "Manufacturing activity is expanding above trend." if pmi['score'] > 0 else "Manufacturing activity remains below trend.",
                "implication": "Positive contribution to cyclical acceleration." if pmi['score'] > 0 else "Drag on broader economic cycle."
            })

        # 2. Industrial Production (IIP)
        if 'IIP' in evals and evals['IIP']['state'] != 'Unknown':
            iip = evals['IIP']
            yoy_str = f"{iip['yoy_value']:.1f}%" if not pd.isna(iip['yoy_value']) else "N/A"
            z = iip['score']
            if z > 1.0:
                iip_interp = "Industrial output is strongly above its historical trend."
            elif z > 0.5:
                iip_interp = "Industrial output is above its historical trend."
            elif z > -0.5:
                iip_interp = "Industrial output is near its historical trend."
            elif z > -1.0:
                iip_interp = "Industrial output is below its historical trend."
            else:
                iip_interp = "Industrial output is significantly below its historical trend."
                
            insights.append({
                "observation": f"Industrial production stands at {iip['raw_value']:.1f} ({yoy_str} YoY).",
                "evidence": f"Z-score = {iip['score']:+.2f}",
                "interpretation": iip_interp,
                "implication": "Supportive of underlying economic momentum." if iip['score'] > 0 else "Limited contribution to cyclical acceleration."
            })

        # 3. Real Policy Rate
        if 'Real Policy Rate' in evals and evals['Real Policy Rate']['state'] != 'Unknown':
            rpr = evals['Real Policy Rate']
            val_str = f"{rpr['raw_value']:.2f}%"
            insights.append({
                "observation": f"Real policy rate stands at {val_str} ({rpr['percentile']}).",
                "evidence": f"Z-score = {rpr['score']:+.2f}",
                "interpretation": "Accommodative real rates support capital investment and credit demand." if rpr['score'] > 0 else "High real rates act as a restrictive monetary headwind.",
                "implication": "Supportive environment for borrowing and cyclical growth." if rpr['score'] > 0 else "Headwind for interest-sensitive sectors."
            })
                
        # 4. Yield Curve (Yield Spread)
        if 'Yield Spread' in evals and evals['Yield Spread']['state'] != 'Unknown':
            ys = evals['Yield Spread']
            shape = "inverted" if ys['raw_value'] < 0 else ("steep" if ys['score'] > 0 else "flat")
            insights.append({
                "observation": f"The yield curve is {shape} with a spread of {ys['raw_value']:.2f}%.",
                "evidence": f"Z-score = {ys['score']:+.2f}",
                "interpretation": "Bond markets are signaling elevated recessionary risks." if ys['raw_value'] < 0 else ("Signals healthy forward-looking growth expectations." if ys['score'] > 0 else "Suggests a moderation in growth expectations."),
                "implication": "Favors high-quality fixed income over equities." if ys['raw_value'] < 0 else "Positive for bank net interest margins." if ys['score'] > 0 else "Neutral signal for broad asset allocation."
            })

        # 5. Inflation (CPI)
        if 'CPI' in evals and evals['CPI']['state'] != 'Unknown':
            cpi = evals['CPI']
            yoy_str = f"{cpi['yoy_value']:.1f}%" if not pd.isna(cpi['yoy_value']) else "N/A (insufficient history)"
            insights.append({
                "observation": f"Consumer Price Index is at {cpi['raw_value']:.1f}, translating to {yoy_str} YoY inflation.",
                "evidence": f"Z-score = {cpi['score']:+.2f}",
                "interpretation": "Inflation remains above its long-run average." if cpi['score'] > 0 else "Inflation remains below its long-run average.",
                "implication": "Potential headwind for policy easing." if cpi['score'] > 0 else "Supportive for duration and broad equity multiples."
            })

        if not insights:
            insights.append({
                "observation": "Insufficient data.",
                "evidence": "N/A",
                "interpretation": "Unable to generate a reliable macro synthesis.",
                "implication": "Maintain neutral benchmark weightings."
            })
            
        return insights
