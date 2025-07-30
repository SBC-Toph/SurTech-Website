#!/usr/bin/env python3
"""
Quick start example - Pylance compatible
Save this as: trading_platform/scripts/quick_start.py
"""

import sys
import os
import time
from pathlib import Path

# Setup Python path BEFORE any imports
current_file = Path(__file__).resolve()

if "scripts" in current_file.parts:
    project_root = current_file.parent.parent
else:
    project_root = current_file.parent

src_path = project_root / "src"

if not src_path.exists():
    print(f"ERROR: Cannot find src directory at {src_path}")
    print(f"Please run this script from trading_platform/scripts/")
    sys.exit(1)

# Add src to Python path
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Now import with type ignore to satisfy Pylance
try:
    from data_generation.live_simulator import LiveMarketSimulator  # type: ignore
except ImportError:
    print("ERROR: Cannot import LiveMarketSimulator")
    print("Please ensure src/data_generation/live_simulator.py exists and has content")
    sys.exit(1)

def main():
    print("Quick Start: Live Market Simulator")
    print("=" * 40)
    
    try:
        # Create a simple simulator
        simulator = LiveMarketSimulator(
            total_points=15,        # Short demo
            initial_price=50,       # Start neutral
            volatility=2.0,         # Good movement
            save_to_csv=True        # Save the data
        )
        
        print(f"Market will resolve: {'YES' if simulator.final_resolution else 'NO'}")
        print(f"Starting price: ${simulator.initial_price}")
        
        # Option 1: Manual stepping
        print("\n--- Manual Mode ---")
        print("Generating 5 points manually:")
        
        for i in range(5):
            data_point = simulator.step()
            if data_point:
                print(f"Point {i+1}: ${data_point['price']:.2f} "
                      f"(volume: {data_point['volume']})")
            else:
                print("Simulation complete!")
                break
        
        # Option 2: Automatic mode
        print("\n--- Automatic Mode ---")
        print("Starting live simulation for 3 seconds...")
        
        simulator.start_live_simulation(time_interval=0.3, mode="auto")
        time.sleep(3)
        simulator.stop()
        
        # Show results
        print(f"\nResults:")
        print(f"Total points generated: {len(simulator.data_history)}")
        print(f"Final price: ${simulator.get_current_price():.2f}")
        
        if simulator.csv_filename:
            print(f"Data saved to: data/market_data/{simulator.csv_filename}")
        
        # Show recent data
        recent = simulator.get_recent_history(5)
        if recent:
            recent_prices = [f"${d['price']:.2f}" for d in recent]
            print(f"\nLast 5 prices: {recent_prices}")
        
        print("\n✅ Quick start completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during simulation: {e}")
        print("Please check that all required files are in place")

if __name__ == "__main__":
    main()