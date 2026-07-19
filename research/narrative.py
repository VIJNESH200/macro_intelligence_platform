# report_narrative.py
import pandas as pd

def generate_narrative(data, analysis, insights, market_insights, analogues):
    quad = insights['phase']
    direction = insights['direction']
    prev_phase = analysis.get('previous_phase', 'Unknown')
    
    health_above = insights['health_above_trend']
    mom_above = insights['momentum_above_trend']
    market_resilient = insights['market_resilient']
    
    health_str = "above trend" if health_above else "below trend"
    mom_str = "strengthening" if mom_above else "weakening"
    early_stage = insights.get('early_stage', False)
    late_stage = insights.get('late_stage', False)
    
    # 1. Macro Thesis (Executive Summary)
    thesis_statement = f"The economy has entered the {quad} phase." if early_stage else f"The economy is currently in a mature {quad} phase."
    
    macro_score = insights.get('macro_score_raw') # Now passing the Z-score sum
    avg_fwd = analogues['averages']['avg_fwd_val'] if analogues and 'averages' in analogues and analogues['averages'] and not pd.isna(analogues['averages']['avg_fwd_val']) else 0
    
    try:
        from ..analytics.macro_intelligence_engine import MacroIntelligenceEngine
    except ImportError:
        from analytics.macro_intelligence_engine import MacroIntelligenceEngine
        
    stance_dict = MacroIntelligenceEngine.generate_overall_stance(macro_score, avg_fwd)
    stance = stance_dict['stance']
    stance_reason = stance_dict['rationale']
        
    if quad == "Expansion":
        evidence = "Despite strong absolute economic health, momentum has begun to decelerate from peak levels." if not mom_above else "Economic activity and momentum both remain robustly above long-term trends."
    elif quad == "Slowdown":
        evidence = "Despite weakening macro momentum, economic activity remains comfortably above trend." if health_above else "Both absolute economic health and momentum are deteriorating."
    elif quad == "Contraction":
        evidence = "Leading indicators confirm a synchronized decline, with both health and momentum well below trend."
    else: # Recovery
        evidence = "While absolute activity remains depressed, positive momentum indicates a nascent macroeconomic turnaround."

    validation = ""
    if analogues and 'averages' in analogues and analogues['averages']:
        avg = analogues['averages']
        validation = f"Historical analogue analysis suggests similar environments have typically resolved into {avg['most_common_next']} while producing {avg['avg_fwd_str']} forward equity returns."
        
    implication = "Current market pricing appears broadly consistent with underlying macro conditions."
    if market_resilient and not mom_above:
        implication = "However, domestic equities currently remain highly resilient, presenting a potential divergence from underlying macro momentum."
    elif not market_resilient and mom_above:
        implication = "Conversely, risk assets remain suppressed despite an observable acceleration in underlying macro momentum."
        
    exec_summary = f"<b>Research Thesis:</b><br/><br/>{thesis_statement}<br/><br/>{evidence}<br/><br/>{validation}<br/><br/>{implication}<br/><br/><b>Overall Stance:</b> {stance}<br/><b>Rationale:</b> {stance_reason}"

    # Key Takeaways
    tk_1 = f"Economic activity remains {health_str} despite {mom_str} momentum." if (health_above and not mom_above) else f"Economic activity is {health_str} while momentum is {mom_str}."
    tk_2 = f"The economy has remained in the {quad} regime for {analysis.get('current_duration_num', 0)} months, completing {analysis.get('completion_pct', 0):.0f}% of its historical average duration."
    
    highest_trans = insights['highest_transition']
    tk_3 = f"Historical transitions from this quadrant resolve most frequently toward {highest_trans} ({insights['highest_transition_prob']:.0f}%)." if highest_trans != "N/A" else f"Directional trajectory indicates {direction} momentum."
    
    tk_4 = "Market performance exhibits a short-term divergence from underlying macro momentum." if market_resilient and not mom_above else "Market performance remains directionally aligned with leading macro indicators."
    
    takeaways = [tk_1, tk_2, tk_3, tk_4]

    # Integrated Market Interpretation (4-Paragraph Thesis)
    if early_stage:
        maturity_str = "an early-stage phase profile"
    elif late_stage:
        maturity_str = "a mature, late-stage phase profile"
    else:
        maturity_str = "a mid-cycle phase profile"
        
    interp_1 = f"At {analysis.get('completion_pct', 0):.0f}% of its historical average duration, the {quad} regime displays {maturity_str}. Its prevailing directional vector is {direction}, pointing toward an eventual shift into {highest_trans}."
    
    interp_2 = ""
    if analogues and 'averages' in analogues and analogues['averages']:
        avg = analogues['averages']
        interp_2 += f"When examining past periods with similar mathematical signatures, cycle dynamics usually progressed into {avg['most_common_next']} over the subsequent {avg['avg_dur_str']}. "
        if not pd.isna(avg['avg_fwd_val']):
            interp_2 += f"This specific macro backdrop has historically provided a {avg['avg_fwd_str']} tailwind for benchmark equities over a six-month horizon."
    else:
        interp_2 += "However, no prior historical regimes cleanly map to the current unique configuration of health and momentum."
        
    interp_3 = ""
    spread_text = ""
    if market_insights and isinstance(market_insights, dict) and 'spread' in market_insights and market_insights['spread'] > 0:
        spread_text = f"We are observing notable internal market divergence, as {market_insights['best_asset']} outperformed {market_insights['worst_asset']} by {market_insights['spread']:.1f} percentage points this past month. "
    
    if market_resilient and not mom_above:
        interp_3 += f"What stands out most is the resilience of domestic risk assets in the face of deteriorating macroeconomic momentum. {spread_text}This pronounced divergence implies that financial markets have yet to fully discount the underlying fundamental deceleration."
    elif not market_resilient and mom_above:
        interp_3 += f"Interestingly, financial markets remain tactically weak despite an observable acceleration in macroeconomic momentum. {spread_text}This dislocation suggests that elevated risk premiums are temporarily overshadowing the fundamental growth recovery."
    else:
        interp_3 += f"Current asset pricing aligns well with these underlying macroeconomic realities and transition probabilities. {spread_text}"
        
    highest_trans_prob = insights.get('highest_transition_prob', 0)
    closing_stmt = ""
    if stance in ["Highly Constructive", "Constructive"]:
        closing_stmt = "Overall, current macro conditions remain broadly supportive, with historical evidence favoring resilience over the medium term while warranting disciplined monitoring of near-term transition risks."
    elif stance in ["Highly Defensive", "Defensive"]:
        closing_stmt = "Overall, current macro conditions demand a defensive posture, with historical evidence suggesting elevated vulnerability over the medium term as fundamental deterioration persists."
    else:
        closing_stmt = "Overall, current macro conditions present a mixed tactical environment, with historical evidence suggesting caution is warranted until a definitive directional break emerges."
        
    interp_4 = f"Synthesizing the {quad} trajectory, empirical precedent, and market behavior, our recommended strategic posture is {stance.lower()}. Moving forward, asset allocation strategies must carefully monitor the {highest_trans_prob:.0f}% probability of a structural break into {highest_trans}. {closing_stmt}"
    
    interp_5 = ""
    forecast = data.get('forecast')
    if forecast and 'forecast_3m' in forecast:
        f3m = forecast['forecast_3m']
        conv = f3m.get('conviction', 50)
        proj_quad = f3m.get('quadrant', 'Unknown')
        interp_5 = f"Based on our three-signal consensus framework, the most probable trajectory over the next 3 months is a continuation into the {proj_quad} phase with {conv:.1f}% conviction."
        
    interp = f"{interp_1}<br/><br/>{interp_2}<br/><br/>{interp_3}<br/><br/>{interp_4}"
    if interp_5:
        interp += f"<br/><br/>{interp_5}"
        
    # Risks to Monitor
    risks = []
    completion = analysis.get('completion_pct', 0)
    highest_prob = insights.get('highest_transition_prob', 0)
    
    if completion > 100 and highest_prob > 60:
        risks.append(f"Regime Shift Risk: The current phase has exceeded its historical average duration, with a highly elevated ({highest_prob:.0f}%) probability of a near-term transition to {highest_trans}.")
        
    if market_resilient and not mom_above:
        risks.append("Macro-Market Divergence: Risk asset valuations may be vulnerable to a rapid repricing if the macro deceleration accelerates.")
        
    if quad == "Expansion":
        risks.append("Margin compression as late-cycle capacity constraints and input costs rise.")
    elif quad == "Slowdown":
        risks.append(f"Monitor whether momentum stabilises or breaks aggressively into {highest_trans if highest_trans != 'N/A' else 'Contraction'}.")
    elif quad == "Contraction":
        risks.append("Systemic credit events or earnings downgrades triggered by sustained economic weakness.")
    else:
        risks.append("A 'false start' where momentum reverses, dragging the cycle back into Contraction.")

    methodology = (
        "<b>Macro Intelligence Engine</b><br/><font size=8>&bull; Multi-factor Z-score sum<br/>&bull; Dynamic Confidence Scoring</font><br/><br/>"
        "<b>Economic Health & Momentum</b><br/><font size=8>&bull; Rolling Z-score<br/>&bull; Normalized monthly change</font><br/><br/>"
        "<b>Market Score</b><br/><font size=8>&bull; Independent signal derived strictly from asset price action<br/>&bull; Composite of multi-horizon price momentum</font><br/><br/>"
        "<b>Analogue Matching</b><br/><font size=8>&bull; Multi-dimensional Euclidean distance (XY + Macro Drivers)</font><br/><br/>"
        "<b>Forecasting Engine</b><br/><font size=8>&bull; 3-Signal Consensus (Momentum, Analogues, Macro Drivers)</font>"
    )

    return {
        'executive_summary': exec_summary,
        'takeaways': takeaways,
        'interpretation': interp,
        'risks': risks,
        'methodology': methodology
    }
