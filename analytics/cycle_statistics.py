"""
Cycle Statistics — Phase durations, transition probabilities.
==============================================================
Exact port of report_analysis.py.
"""


def compute_statistics(df, data: dict) -> dict:
    """Compute historical cycle statistics for the current phase.

    Segments the full Quadrant history into consecutive phase runs.
    For the current quadrant, calculates average/min/max duration
    and the transition probability matrix.
    """
    quads = df['Quadrant'].tolist()
    if not quads:
        return {}

    current_quad = data['quadrant']

    phases = []
    current_phase = quads[0]
    count = 1
    for q in quads[1:]:
        if q == current_phase:
            count += 1
        else:
            phases.append((current_phase, count))
            current_phase = q
            count = 1
    phases.append((current_phase, count))

    # Current duration
    current_duration = phases[-1][1]

    # Look back at historical phases matching current_quad
    historical_matches = [c for phase, c in phases[:-1] if phase == current_quad]

    if historical_matches:
        avg_dur = sum(historical_matches) / len(historical_matches)
        max_dur = max(historical_matches)
        min_dur = min(historical_matches)
        occurrences = len(historical_matches) + 1  # include current
    else:
        avg_dur = current_duration
        max_dur = current_duration
        min_dur = current_duration
        occurrences = 1

    dur_diff = current_duration - avg_dur

    next_phases = []
    for i in range(len(phases) - 1):
        if phases[i][0] == current_quad:
            next_phases.append(phases[i + 1][0])

    most_common_next = "N/A"
    if next_phases:
        most_common_next = max(set(next_phases), key=next_phases.count)
        prob = (next_phases.count(most_common_next) / len(next_phases)) * 100
        transition_str = f"{most_common_next} ({prob:.0f}%)"

        # Calculate full transition probabilities mapping
        transition_probs = {}
        total = len(next_phases)
        for phase in set(next_phases):
            transition_probs[phase] = (next_phases.count(phase) / total) * 100
    else:
        transition_str = "N/A"
        transition_probs = {}

    idx = len(quads) - 1
    entered_idx = max(0, idx - current_duration + 1)
    entered_date = df.iloc[entered_idx].name.strftime('%b %Y')
    prev_phase = phases[-2][0] if len(phases) > 1 else "N/A"

    completion_pct = (current_duration / max(1, avg_dur)) * 100

    return {
        'current_duration': f"{current_duration} months",
        'avg_duration': f"{avg_dur:.1f} months",
        'longest_duration': f"{max_dur} months",
        'shortest_duration': f"{min_dur} months",
        'occurrences': occurrences,
        'transition_after': transition_str,
        'entered_date': entered_date,
        'previous_phase': prev_phase,
        # Raw numericals for narrative generation & Historical Context table
        'current_duration_num': current_duration,
        'avg_duration_num': avg_dur,
        'duration_diff_num': dur_diff,
        'completion_pct': completion_pct,
        'most_common_next_str': most_common_next,
        'transition_probs': transition_probs
    }
