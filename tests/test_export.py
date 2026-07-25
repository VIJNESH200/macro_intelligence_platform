from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.data_engine import DataEngine
from features.feature_engine import FeatureEngine
from analytics.macro_intelligence_engine import MacroIntelligenceEngine
from analytics.research_engine import ResearchEngine
from config import CONFIG, MARKET_SERIES, MACRO_SERIES
from research.pdf import build_pdf_report
from datetime import datetime
import pandas as pd

# Load data
engine = DataEngine(CONFIG, MARKET_SERIES, MACRO_SERIES)
df = engine.load_all()
df, spline_data = FeatureEngine.compute_all(df, CONFIG)

# Eval
idx = len(df.dropna()) - 1 if len(df.dropna()) > 0 else len(df) - 1
evals = MacroIntelligenceEngine.evaluate_indicators(df, idx)
res = MacroIntelligenceEngine.assign_contribution(df, idx)
macro_contrib = {
    'all_drivers': res['all_drivers'],
    'macro_score': res['macro_score'],
    'rationale': res['confidence_rationale'],
    'confidence_score': res['confidence_score'],
    'confidence_rationale': res['confidence_rationale'],
    'macro_interpretation': res['macro_interpretation']
}

data = {
    'indicator': CONFIG['name'],
    'date': datetime.now().strftime('%B %Y'),
    'source': CONFIG['source'],
    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
    'window': f"{CONFIG['window']}-Month Rolling",
    'quadrant': 'Expansion',
    'macro_contrib': macro_contrib,
    'market_data': [],
    'transition_matrix': None,
    'forecast': None,
    'scenarios': []
}

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

if not os.path.exists('exports'):
    os.makedirs('exports')

fig, ax = plt.subplots()
ax.plot([0, 1], [0, 1])
temp_fig = "temp_fig.png"
fig.savefig(temp_fig)
plt.close(fig)

out_pdf = 'exports/test_report.pdf'
build_pdf_report(
    data=data,
    analysis={},
    insights={'phase': 'Expansion', 'direction': 'Up', 'health_above_trend': True, 'momentum_above_trend': True, 'market_resilient': True, 'highest_transition': 'N/A', 'highest_transition_prob': 0.0, 'completion_pct': 0.0, 'highest_trans': 'Slowdown', 'highest_trans_prob': 0.0},
    market_insights={},
    narrative={'executive_summary': 'test', 'takeaways': [], 'interpretation': 'test', 'risks': [], 'methodology': 'test'},
    analogues={},
    deltas=[],
    chart_path=temp_fig,
    output_path=out_pdf,
    data_metadata=engine.get_metadata
)
print("PDF Exported Successfully!")

if os.path.exists(temp_fig):
    os.remove(temp_fig)
if os.path.exists(out_pdf):
    os.remove(out_pdf)
