"""
Configuration settings for the trading platform
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Database settings
DATABASE_CONFIG = {
    "sqlite": {
        "path": BASE_DIR / "data" / "databases" / "trading_platform.db",
        "test_path": BASE_DIR / "data" / "databases" / "test_trading.db"
    }
}

# Market data settings
MARKET_DATA_CONFIG = {
    "batch_data_dir": BASE_DIR / "data" / "market_data" / "batch",
    "live_data_dir": BASE_DIR / "data" / "market_data" / "live",
    "export_dir": BASE_DIR / "data" / "exports"
}

# Simulation settings
SIMULATION_CONFIG = {
    "default_total_points": 1500,
    "default_initial_price": 50.0,
    "default_volatility": 1.8,
    "default_time_interval": 1.0,
    "max_time_interval": 10.0,
    "min_time_interval": 0.1
}

# Portfolio settings
PORTFOLIO_CONFIG = {
    "default_starting_cash": 15000.0,
    "available_strikes": [0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
    "max_position_percentage": 0.2,  # Max 20% of cash in any position
    "min_liquidity": 10  # Minimum contracts available
}

# API settings
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": os.getenv("DEBUG", "False").lower() == "true"
}

# Logging settings
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_dir": BASE_DIR / "logs"
}
