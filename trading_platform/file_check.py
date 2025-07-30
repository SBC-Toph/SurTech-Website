#!/usr/bin/env python3
"""
Simple script to check what files exist
Save this as: trading_platform/check_files.py
"""

import os
from pathlib import Path

def main():
    print("QUICK FILE CHECK")
    print("=" * 30)
    
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    
    # Key files to check
    key_files = [
        "src/data_generation/live_simulator.py",
        "src/pricing/option_pricing.py", 
        "src/portfolio/portfolio_manager.py",
        "scripts/quick_start.py"
    ]
    
    print(f"\nChecking key files:")
    for file_path in key_files:
        full_path = current_dir / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"✓ {file_path} ({size:,} bytes)")
        else:
            print(f"✗ {file_path} - MISSING")
    
    # Check if live_simulator.py specifically exists
    live_sim_path = current_dir / "src/data_generation/live_simulator.py"
    
    print(f"\nSpecific check for live_simulator.py:")
    print(f"Path: {live_sim_path}")
    print(f"Exists: {live_sim_path.exists()}")
    
    if not live_sim_path.exists():
        print(f"\n❌ PROBLEM FOUND:")
        print(f"The file src/data_generation/live_simulator.py does NOT exist!")
        print(f"This is why you're getting the import error.")
        print(f"\nTO FIX:")
        print(f"1. Copy the LiveMarketSimulator code I provided")
        print(f"2. Save it as: src/data_generation/live_simulator.py")
        print(f"3. Make sure it's in the exact location above")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")