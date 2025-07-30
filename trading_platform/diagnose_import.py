#!/usr/bin/env python3
"""
Diagnostic script to check import issues
Save this as: trading_platform/diagnose_import.py
"""

import sys
import os
from pathlib import Path

def main():
    print("IMPORT DIAGNOSTIC")
    print("=" * 50)
    
    # Check current directory
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    
    # Check if we're in the right place
    if not (current_dir / "src").exists():
        print("❌ Not in trading_platform directory!")
        print("Please navigate to trading_platform/ first")
        return
    
    # Check file existence and content
    live_sim_path = current_dir / "src" / "data_generation" / "live_simulator.py"
    print(f"\nChecking: {live_sim_path}")
    
    if not live_sim_path.exists():
        print("❌ File does NOT exist!")
        print("You need to create src/data_generation/live_simulator.py")
        return
    
    # Check file size
    file_size = live_sim_path.stat().st_size
    print(f"✓ File exists, size: {file_size:,} bytes")
    
    if file_size == 0:
        print("❌ File is EMPTY!")
        print("You need to add the LiveMarketSimulator code to this file")
        return
    
    # Check file content
    try:
        with open(live_sim_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key components
        if 'class LiveMarketSimulator' in content:
            print("✓ LiveMarketSimulator class found in file")
        else:
            print("❌ LiveMarketSimulator class NOT found in file")
            print("The file exists but doesn't contain the class definition")
            return
            
        if 'def __init__' in content:
            print("✓ __init__ method found")
        else:
            print("❌ __init__ method not found")
            
        # Check imports
        required_imports = ['import threading', 'import pandas', 'import numpy']
        for imp in required_imports:
            if imp in content:
                print(f"✓ Found: {imp}")
            else:
                print(f"❌ Missing: {imp}")
                
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    # Check __init__.py files
    print(f"\nChecking __init__.py files:")
    init_files = [
        "src/__init__.py",
        "src/data_generation/__init__.py"
    ]
    
    for init_file in init_files:
        init_path = current_dir / init_file
        if init_path.exists():
            print(f"✓ {init_file}")
        else:
            print(f"❌ {init_file} MISSING")
            # Create it
            try:
                init_path.touch()
                print(f"  → Created {init_file}")
            except Exception as e:
                print(f"  → Failed to create: {e}")
    
    # Test the actual import
    print(f"\nTesting import:")
    
    # Add src to path
    src_path = current_dir / "src"
    sys.path.insert(0, str(src_path))
    print(f"Added to path: {src_path}")
    
    try:
        # Try importing the module first
        import data_generation.live_simulator as sim_module
        print("✓ Module imported successfully")
        
        # Check if class exists in module
        if hasattr(sim_module, 'LiveMarketSimulator'):
            print("✓ LiveMarketSimulator class found in module")
            
            # Try to instantiate it
            simulator = sim_module.LiveMarketSimulator(total_points=5, save_to_csv=False)
            print("✓ LiveMarketSimulator instance created successfully")
            print("🎉 IMPORT TEST PASSED!")
            
        else:
            print("❌ LiveMarketSimulator class not found in module")
            print("Available attributes:", dir(sim_module))
            
    except SyntaxError as e:
        print(f"❌ SYNTAX ERROR in live_simulator.py:")
        print(f"  Line {e.lineno}: {e.text}")
        print(f"  Error: {e.msg}")
        print("Fix the syntax error in the file")
        
    except ImportError as e:
        print(f"❌ IMPORT ERROR: {e}")
        print("Check that all required dependencies are installed")
        
    except Exception as e:
        print(f"❌ OTHER ERROR: {e}")
        print("There's an issue with the code in live_simulator.py")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")