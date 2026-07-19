"""
Deltas — Month-over-month change computation.
===============================================
Port of report_deltas.py with updated import paths.
"""
try:
    from ..research import report_data
    from . import cycle_statistics
    from . import insights as insights_module
except ImportError:
    from research import report_data
    import analytics.cycle_statistics as cycle_statistics
    import analytics.insights as insights_module


def calculate_deltas(df, current_idx: int, CONFIG: dict, plot_elements: dict,
                     MARKET_SERIES: dict, current_data: dict,
                     current_analysis: dict, current_insights: dict) -> dict | None:
    """Compute month-over-month changes by re-running the pipeline for the previous month."""
    if current_idx < 1:
        return None  # No previous data

    prev_idx = current_idx - 1
    df_prev_sliced = df.iloc[:prev_idx + 1]

    # Run the entire pipeline for the previous month
    prev_data = report_data.extract_report_data(df, CONFIG, plot_elements, prev_idx, MARKET_SERIES)
    prev_analysis = cycle_statistics.compute_statistics(df_prev_sliced, prev_data)
    prev_insights = insights_module.generate_insights(prev_data, prev_analysis)

    # Calculate Deltas
    health_delta = current_data['health_val'] - prev_data['health_val']
    momentum_delta = current_data['momentum_val'] - prev_data['momentum_val']

    # Transition Prob Delta
    curr_prob = current_insights.get('highest_transition_prob', 0)
    prev_prob = prev_insights.get('highest_transition_prob', 0)
    prob_delta = curr_prob - prev_prob

    # Confidence Delta
    curr_conf = current_insights['confidence']['score']
    prev_conf = prev_insights['confidence']['score']
    conf_delta = curr_conf - prev_conf

    # Determine what drove the change
    drivers = []
    if current_data['quadrant'] != prev_data['quadrant']:
        drivers.append(f"Regime transition from {prev_data['quadrant']} to {current_data['quadrant']}")

    if abs(momentum_delta) >= 0.01:
        dir_word = "strengthened" if momentum_delta > 0 else "weakened"
        drivers.append(f"Economic Momentum {dir_word} by {abs(momentum_delta):.2f} standard deviations")

    if abs(conf_delta) >= 1:
        dir_word = "increased" if conf_delta > 0 else "decreased"
        drivers.append(f"Macro Score {dir_word} by {abs(conf_delta):.0f} points")

    dur = current_analysis.get('current_duration_num', 0)
    if dur > 1 and current_data['quadrant'] == prev_data['quadrant']:
        drivers.append(f"Phase duration increased to {dur} months")

    if not drivers:
        drivers.append("No significant quantitative shifts detected this month")

    # Generate a narrative context
    if current_data['quadrant'] == prev_data['quadrant']:
        change_narrative = (
            f"The economy remains in {current_data['quadrant']}. "
            f"Momentum shifted by {momentum_delta:+.2f}, while confidence "
            f"changed by {conf_delta:+} points."
        )
    else:
        change_narrative = (
            f"A regime transition occurred this month from {prev_data['quadrant']} "
            f"to {current_data['quadrant']}. This was driven by a momentum change "
            f"of {momentum_delta:+.2f}."
        )

    return {
        'prev_date': prev_data['date'],
        'prev_phase': prev_data['quadrant'],
        'prev_health': prev_data['health_val'],
        'prev_momentum': prev_data['momentum_val'],
        'prev_transition_prob': prev_prob,
        'prev_confidence': prev_conf,
        'health_delta': health_delta,
        'momentum_delta': momentum_delta,
        'prob_delta': prob_delta,
        'conf_delta': conf_delta,
        'drivers': drivers,
        'change_narrative': change_narrative
    }
