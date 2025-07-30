import pandas as pd
import numpy as np

def compute_option_prices_from_df(
    df: pd.DataFrame,
    strike_price: float = 0.5,
    decay_rate: float = 1.5,
    yes_col: str = 'yes_price',
    no_col: str = 'no_price'
) -> pd.DataFrame:
    """
    Compute option bid/ask prices with exponential time decay from a probability DataFrame.

    Parameters:
        df (pd.DataFrame): DataFrame containing yes_price and no_price columns.
        strike_price (float): Strike price of the option (e.g. 0.5 for ATM).
        decay_rate (float): Speed of exponential time decay (k).
        yes_col (str): Column name for yes-side price (default = 'yes_price').
        no_col (str): Column name for no-side price (default = 'no_price').

    Returns:
        pd.DataFrame: The original DataFrame with new columns:
                      't_index', 'decay_multiplier', 'option_bid', 'option_ask'.
    """
    df = df.copy()
    T = len(df) - 1
    df['t_index'] = range(len(df))
    
    df['decay_multiplier'] = np.exp(-decay_rate * (df['t_index'].to_numpy() / T))

    df['option_bid'] = df[yes_col] * (1 - strike_price) * df['decay_multiplier']
    df['option_ask'] = (1 - df[no_col]) * (1 - strike_price) * df['decay_multiplier']

    return df
