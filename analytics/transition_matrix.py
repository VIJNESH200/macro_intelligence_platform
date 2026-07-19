"""
Transition Matrix — Full 4×4 Markov transition probability matrix.
===================================================================
Generalizes cycle_statistics.py to compute transition probabilities
between ALL quadrant pairs, not just from the current quadrant.
"""
import numpy as np
import pandas as pd


QUADRANT_ORDER = ['Expansion', 'Slowdown', 'Contraction', 'Recovery']


def compute_transition_matrix(df: pd.DataFrame) -> dict:
    """Compute the full 4×4 Markov transition probability matrix.

    Returns a dict with:
        'matrix': 4×4 numpy array of probabilities (rows = from, cols = to)
        'labels': list of quadrant names in order
        'counts': 4×4 numpy array of raw transition counts
        'durations': dict mapping quadrant -> {'mean': float, 'std': float, 'min': int, 'max': int}
        'steady_state': 4-element array of long-run equilibrium probabilities
    """
    if 'Quadrant' not in df.columns or len(df) < 2:
        return _empty_result()

    quads = df['Quadrant'].tolist()

    # 1. Segment into consecutive phase runs
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

    # 2. Build transition count matrix
    n = len(QUADRANT_ORDER)
    counts = np.zeros((n, n), dtype=int)
    idx_map = {q: i for i, q in enumerate(QUADRANT_ORDER)}

    for i in range(len(phases) - 1):
        from_q = phases[i][0]
        to_q = phases[i + 1][0]
        if from_q in idx_map and to_q in idx_map:
            counts[idx_map[from_q], idx_map[to_q]] += 1

    # 3. Normalize to probabilities
    row_sums = counts.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums == 0, 1, row_sums)  # avoid division by zero
    matrix = counts / row_sums

    # 4. Duration statistics per quadrant
    durations = {}
    for q in QUADRANT_ORDER:
        q_durs = [dur for phase, dur in phases if phase == q]
        if q_durs:
            durations[q] = {
                'mean': np.mean(q_durs),
                'std': np.std(q_durs),
                'min': int(np.min(q_durs)),
                'max': int(np.max(q_durs)),
                'count': len(q_durs)
            }
        else:
            durations[q] = {'mean': 0.0, 'std': 0.0, 'min': 0, 'max': 0, 'count': 0}

    # 5. Steady-state distribution (eigenvector of transition matrix)
    steady_state = _compute_steady_state(matrix)

    return {
        'matrix': matrix,
        'labels': QUADRANT_ORDER,
        'counts': counts,
        'durations': durations,
        'steady_state': steady_state
    }


def _compute_steady_state(P: np.ndarray) -> np.ndarray:
    """Compute the stationary distribution of a Markov chain via eigen-decomposition."""
    try:
        eigenvalues, eigenvectors = np.linalg.eig(P.T)
        # Find eigenvector corresponding to eigenvalue ≈ 1
        idx = np.argmin(np.abs(eigenvalues - 1.0))
        stationary = np.real(eigenvectors[:, idx])
        stationary = stationary / stationary.sum()
        # Ensure non-negative
        stationary = np.maximum(stationary, 0)
        stationary = stationary / stationary.sum()
        return stationary
    except Exception:
        return np.ones(len(QUADRANT_ORDER)) / len(QUADRANT_ORDER)


def get_transition_probs_from(matrix: np.ndarray, quadrant: str) -> dict:
    """Get transition probabilities from a specific quadrant.

    Returns dict mapping destination quadrant -> probability (0-100).
    """
    if quadrant not in QUADRANT_ORDER:
        return {}
    idx = QUADRANT_ORDER.index(quadrant)
    return {q: matrix[idx, j] * 100 for j, q in enumerate(QUADRANT_ORDER)}


def _empty_result() -> dict:
    n = len(QUADRANT_ORDER)
    return {
        'matrix': np.zeros((n, n)),
        'labels': QUADRANT_ORDER,
        'counts': np.zeros((n, n), dtype=int),
        'durations': {q: {'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'count': 0} for q in QUADRANT_ORDER},
        'steady_state': np.ones(n) / n
    }
