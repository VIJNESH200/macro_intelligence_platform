import pandas as pd

def calculate_rrg_metrics(asset_prices: pd.Series, benchmark_prices: pd.Series, window: int = 14) -> pd.DataFrame:
    """
    Calculate Relative Rotation Graph (RRG) metrics (RS-Ratio and RS-Momentum).
    
    Args:
        asset_prices (pd.Series): Price series of the asset.
        benchmark_prices (pd.Series): Price series of the benchmark.
        window (int): Rolling window period.
        
    Returns:
        pd.DataFrame: DataFrame containing 'rs_ratio' and 'rs_momentum'.
    """
    # Relative Strength (RS)
    rs = asset_prices / benchmark_prices
    
    # RS-Ratio: normalized RS
    # Normalizing by rolling mean to center around 100
    rs_ratio = 100.0 * (rs / rs.rolling(window=window).mean())
    
    # RS-Momentum: rate of change / momentum of RS-Ratio
    rs_momentum = 100.0 * (rs_ratio / rs_ratio.rolling(window=window).mean())
    
    return pd.DataFrame({
        'rs_ratio': rs_ratio,
        'rs_momentum': rs_momentum
    })
