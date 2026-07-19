"""
Insights — Analytical flags, risk levels, confidence scores, alerts.
====================================================================
Exact port of report_insights.py.
"""


def generate_insights(report_data: dict, analysis_results: dict) -> dict:
    """Transforms raw data and statistical analysis into structured analytical insights.

    Returns a dictionary of deterministic boolean flags, risk categorizations,
    confidence scores, and analytical alerts for consumption by the narrative engine.
    """

    # Extract baseline metrics
    phase = report_data.get('quadrant', 'Unknown')
    phase_duration = analysis_results.get('current_duration_num', 1)
    hist_avg = analysis_results.get('avg_duration_num', 1.0)

    center = report_data.get('center', 100)
    health = report_data.get('health_val', center)
    momentum = report_data.get('momentum_val', center)
    distance = report_data.get('distance', 0)
    direction = report_data.get('direction', 'Neutral')

    trans_probs = analysis_results.get('transition_probs', {})
    highest_trans = analysis_results.get('most_common_next_str', 'Unknown')
    highest_trans_prob = trans_probs.get(highest_trans, 0) if highest_trans != 'N/A' else 0

    # Boolean logic mapping
    early_stage = phase_duration < (hist_avg * 0.33)
    late_stage = phase_duration > (hist_avg * 0.75)

    health_above = health >= center
    mom_above = momentum >= center

    # Risk Level mapping
    risk_level = "Low"
    if highest_trans == "Contraction" and highest_trans_prob > 60:
        if not mom_above and not health_above:
            risk_level = "High"
        elif not mom_above:
            risk_level = "Medium"
    elif phase == "Contraction":
        risk_level = "High"
    elif phase == "Slowdown" and late_stage:
        risk_level = "Medium"

    # Confidence Score (0-100) and Contributors
    stability_score = min(40, (phase_duration / max(1, hist_avg)) * 40)
    magnitude_score = min(30, (distance / max(1, distance + 1)) * 30)  # Soft normalization
    predictability_score = min(30, (highest_trans_prob / 100.0) * 30)
    confidence_score = int(stability_score + magnitude_score + predictability_score)

    contributors = []
    if direction in ['Southwest', 'Northwest', 'Northeast', 'Southeast']:
        contributors.append("✓ Stable directional momentum")
    else:
        contributors.append("✗ Neutral/Flat direction")

    if highest_trans_prob > 60:
        contributors.append(f"✓ High transition probability ({highest_trans_prob:.0f}%)")
    else:
        contributors.append("✗ Dispersed historical transitions")

    if distance > 1.5:
        contributors.append("✓ Large distance from center")
    else:
        contributors.append("✗ Proximity to trend center")

    if early_stage:
        contributors.append("✗ Very early phase")
    elif late_stage:
        contributors.append("✓ Established, mature phase")

    # Market resilience check (simplified example)
    market_resilient = True
    for asset in report_data.get('market_data', []):
        if 'Nifty' in asset['name'] or 'S&P' in asset['name']:
            if asset['returns_raw'].get('1M', 0) < 0:
                market_resilient = False
                break

    # Historical Context phrasing
    if phase_duration < hist_avg:
        hist_context = f"Current {phase.lower()} remains shorter than the historical average."
    else:
        hist_context = f"Current {phase.lower()} is exceeding the historical average."

    # Analytical Alerts Generation
    alerts = []

    if mom_above:
        alerts.append("Momentum has strengthened above long-term trend.")
    else:
        alerts.append("Momentum has weakened below long-term trend.")

    if health_above:
        alerts.append("Aggregate economic health remains robust and above trend.")
    else:
        alerts.append("Aggregate economic health resides below trend.")

    if early_stage:
        alerts.append(f"The {phase.lower()} regime remains in its early stages.")
    elif late_stage:
        alerts.append(f"The {phase.lower()} regime is mature and demonstrating late-stage characteristics.")

    if highest_trans != "N/A" and highest_trans_prob > 0:
        alerts.append(f"Highest historical transition probability is toward {highest_trans} ({highest_trans_prob:.0f}%).")

    if risk_level == "High":
        alerts.append("Macroeconomic risk metrics are currently elevated.")

    # Calculate Macro Score
    # Normalize health and momentum assuming standard deviations ~ 1.5
    h_norm = (health - center) * 15
    m_norm = (momentum - center) * 15
    macro_score = int(max(0, min(100, 50 + h_norm + m_norm)))
    
    macro_score_raw = report_data.get('macro_contrib', {}).get('macro_score')

    return {
        "phase": phase,
        "phase_duration": phase_duration,
        "historical_average_duration": hist_avg,
        "early_stage": early_stage,
        "late_stage": late_stage,
        "health_above_trend": health_above,
        "momentum_above_trend": mom_above,
        "direction": direction,
        "transition_probability": trans_probs,
        "highest_transition": highest_trans,
        "highest_transition_prob": highest_trans_prob,
        "risk_level": risk_level,
        "historical_context": hist_context,
        "market_resilient": market_resilient,
        "distance_from_center": distance,
        "macro_score": macro_score,
        "macro_score_raw": macro_score_raw,
        "confidence": {
            "score": confidence_score,
            "contributors": contributors
        },
        "alerts": alerts
    }
