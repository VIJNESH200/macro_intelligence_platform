import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import CONFIG, MACRO_SERIES, MARKET_SERIES
from data.data_engine import DataEngine
from features.feature_engine import FeatureEngine
from analytics.macro_intelligence_engine import MacroIntelligenceEngine

def run_tests():
    print("Testing Macro Intelligence Engine Pipeline...")
    
    # 1. Load Data
    engine = DataEngine(CONFIG, MARKET_SERIES, MACRO_SERIES)
    df = engine.load_all()
    print(f"Loaded DataFrame shape: {df.shape}")
    
    # 2. Features
    df, _ = FeatureEngine.compute_all(df, CONFIG)
    print("Computed Features successfully.")
    
    # 3. Macro Intelligence Engine
    idx = len(df) - 1
    evals = MacroIntelligenceEngine.evaluate_indicators(df, idx)
    print("\n--- Individual Indicator Evaluations ---")
    for name, data in evals.items():
        print(f"{name}: {data['score']:.2f} ({data['state']})")
        
    contrib = MacroIntelligenceEngine.assign_contribution(df, idx)
    print("\n--- Macro Score ---")
    print(f"Total Score: {contrib['macro_score']:.2f}")
    
    shifts = MacroIntelligenceEngine.detect_regime_shifts(df, idx)
    print("\n--- Regime Shifts ---")
    if shifts:
        for s in shifts:
            print(f"- {s}")
    else:
        print("None detected this month.")
        
    print("\nPipeline Test: PASS")

if __name__ == "__main__":
    run_tests()
