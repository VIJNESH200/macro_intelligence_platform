import pandas as pd
from .macro_intelligence_engine import MacroIntelligenceEngine

class ResearchEngine:
    """Institutional Narrative Generation Engine for Macro Intelligence.
    
    Synthesizes quantitative metrics (Z-Scores, YoY variations, Percentiles) into 
    fluid, professional macro research notes inspired by S&P Global Market Intelligence.
    """

    @staticmethod
    def generate_insights(df: pd.DataFrame, idx: int) -> list[dict]:
        evals = MacroIntelligenceEngine.evaluate_indicators(df, idx)
        insights = []
        
        # 1. Core Industries (ICI)
        if 'ICI' in evals and evals['ICI']['state'] != 'Unknown':
            ici = evals['ICI']
            yoy_val = ici.get('yoy_value', 0)
            yoy_str = f"{yoy_val:+.1f}%" if not pd.isna(yoy_val) else "N/A"
            z = ici['score']
            pct = ici.get('percentile', '50th percentile')
            
            if z > 0.5:
                interp = f"Industrial activity demonstrates strong structural velocity, expanding at {yoy_str} YoY and tracking in the upper tier ({pct}) of historical expansion cycles."
                imp = "Provides robust fundamental support for cyclical equity sectors, industrial capex, and macro momentum."
            elif z > -0.5:
                interp = f"Industrial output reflects a mid-cycle consolidation phase, tracking near long-term trend at {yoy_str} YoY ({pct})."
                imp = "Suggests steady underlying industrial demand without immediate supply-chain overheating or severe contractionary risks."
            else:
                interp = f"Industrial momentum is experiencing cyclical drag, printing at {yoy_str} YoY ({pct}) and operating significantly below historical trend velocity."
                imp = "Presents a headwind for broad GDP acceleration, warranting defensive positioning in heavy cyclical assets."
                
            insights.append({
                "title": "Industrial Infrastructure & Core Momentum",
                "narrative": f"{interp} With a standardized Z-score of {z:+.2f}, this baseline momentum {imp.lower()}",
                "observation": f"Core Industries momentum is tracking at {yoy_str} YoY ({pct}).",
                "evidence": f"Z-score = {z:+.2f}",
                "interpretation": interp,
                "implication": imp
            })

        # 2. Real Policy Rate
        if 'Real Policy Rate' in evals and evals['Real Policy Rate']['state'] != 'Unknown':
            rpr = evals['Real Policy Rate']
            val = rpr['raw_value']
            z = rpr['score']
            pct = rpr.get('percentile', '50th percentile')
            
            if val > 2.0:
                interp = f"Real policy rates stand elevated at {val:.2f}% ({pct}), representing a restrictive monetary stance designed to anchor inflation expectations."
                imp = "Acts as a financial headwind for highly leveraged balance sheets while incentivizing conservative corporate capital allocation."
            elif val >= 0:
                interp = f"Real policy rates reside in a neutral-to-supportive corridor at {val:.2f}% ({pct}), maintaining monetary equilibrium between growth and inflation."
                imp = "Provides a balanced credit backdrop, supporting corporate borrowing and capital investment without destabilizing price stability."
            else:
                interp = f"Real policy rates remain deeply accommodative at {val:.2f}% ({pct}), creating highly favorable financial conditions."
                imp = "Encourages risk-taking, corporate borrowing, and asset price expansion, though requiring vigilance for inflation resurgence."

            insights.append({
                "title": "Monetary Transmission & Capital Cost Dynamics",
                "narrative": f"{interp} Standardized financial conditions (Z-score: {z:+.2f}) {imp.lower()}",
                "observation": f"Real policy rate stands at {val:.2f}% ({pct}).",
                "evidence": f"Z-score = {z:+.2f}",
                "interpretation": interp,
                "implication": imp
            })
                
        # 3. Yield Curve (Yield Spread)
        if 'Yield Spread' in evals and evals['Yield Spread']['state'] != 'Unknown':
            ys = evals['Yield Spread']
            val = ys['raw_value']
            z = ys['score']
            pct = ys.get('percentile', '50th percentile')
            
            if val < 0:
                interp = f"The yield curve is inverted at {val:.2f}% spread ({pct}), reflecting bond market pricing of elevated late-cycle recessionary risks."
                imp = "Historically favors high-quality fixed income over equities, suggesting defensive asset allocation."
            elif z > 0.5:
                interp = f"The yield curve displays healthy steepening at a +{val:.2f}% spread ({pct}), signaling robust forward-looking growth and credit demand."
                imp = "Positive for commercial bank net interest margins (NIMs) and supportive of pro-cyclical risk assets."
            else:
                interp = f"The yield curve remains flat at a +{val:.2f}% spread ({pct}), indicating transitional growth expectations among fixed income participants."
                imp = "Recommends neutral duration posture and balanced cross-asset allocation."

            insights.append({
                "title": "Term Structure & Fixed Income Signals",
                "narrative": f"{interp} Term premium dynamics (Z-score: {z:+.2f}) {imp.lower()}",
                "observation": f"Yield spread stands at {val:.2f}% ({pct}).",
                "evidence": f"Z-score = {z:+.2f}",
                "interpretation": interp,
                "implication": imp
            })

        # 4. Inflation (CPI)
        if 'CPI' in evals and evals['CPI']['state'] != 'Unknown':
            cpi = evals['CPI']
            val = cpi['raw_value']
            yoy = cpi.get('yoy_value', 0)
            yoy_str = f"{yoy:+.1f}%" if not pd.isna(yoy) else "N/A"
            z = cpi['score']
            pct = cpi.get('percentile', '50th percentile')
            
            if z > 0.5:
                interp = f"Consumer price pressures are tracking elevated at {yoy_str} YoY ({pct}), remaining above central bank target midpoints."
                imp = "Constrains monetary policy easing space and poses input-cost headwinds for consumer discretionary margin expansion."
            elif z > -0.5:
                interp = f"Consumer inflation remains well-anchored at {yoy_str} YoY ({pct}), aligning with long-term target bands."
                imp = "Provides essential policy flexibility for monetary authorities while preserving household purchasing power."
            else:
                interp = f"Inflation dynamics reflect benign price pressures at {yoy_str} YoY ({pct}), residing below historical average velocity."
                imp = "Highly supportive of fixed income duration and provides expansionary runway for monetary stimulus."

            insights.append({
                "title": "Consumer Inflation & Purchasing Power",
                "narrative": f"{interp} Inflation Z-score ({z:+.2f}) {imp.lower()}",
                "observation": f"CPI stands at {val:.1f} ({yoy_str} YoY, {pct}).",
                "evidence": f"Z-score = {z:+.2f}",
                "interpretation": interp,
                "implication": imp
            })

        if not insights:
            insights.append({
                "title": "Macroeconomic Data Assessment",
                "narrative": "Insufficient data available for full structural synthesis.",
                "observation": "Insufficient data.",
                "evidence": "N/A",
                "interpretation": "Unable to generate a reliable macro synthesis.",
                "implication": "Maintain neutral benchmark weightings."
            })
            
        return insights
