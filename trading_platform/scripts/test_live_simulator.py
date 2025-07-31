#!/usr/bin/env python3
"""
Test script for the live market simulator - Pylance compatible
Save this as: trading_platform/scripts/test_live_simulator.py
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

# Import modules with type ignore to satisfy Pylance
try:
    from data_generation.live_simulator import LiveMarketSimulator, PortfolioIntegrator  # type: ignore
    from portfolio.portfolio_manager import PortfolioManager, TradeType  # type: ignore
    import pandas as pd  # type: ignore
except ImportError as e:
    print(f"ERROR: Cannot import required modules: {e}")
    print("Please ensure these files exist:")
    print("  - src/data_generation/live_simulator.py")
    print("  - src/portfolio/portfolio_manager.py")
    sys.exit(1)

def test_basic_simulator():
    """Test 1: Basic simulator functionality"""
    print("=" * 50)
    print("TEST 1: Basic Live Simulator")
    print("=" * 50)
    
    try:
        simulator = LiveMarketSimulator(
            total_points=20,
            initial_price=50,
            volatility=1.5,
            save_to_csv=True
        )
        
        print(f"Created simulator:")
        print(f"  Will resolve: {'YES' if simulator.final_resolution else 'NO'}")
        print(f"  Total points: {simulator.total_points}")
        print(f"  Initial price: ${simulator.initial_price}")
        
        # Test manual stepping
        print(f"\nTesting manual stepping (first 5 points):")
        for i in range(5):
            data_point = simulator.step()
            if data_point:
                print(f"  Point {i+1}: ${data_point['price']:.2f} "
                      f"(movement: {data_point['movement']:+.2f}, "
                      f"volume: {data_point['volume']})")
            else:
                print("  Simulation complete!")
                break
        
        # Get current stats
        stats = simulator.get_simulation_stats()
        print(f"\nCurrent status:")
        print(f"  Progress: {stats['progress_percent']:.1f}%")
        print(f"  Current price: ${stats['current_price']:.2f}")
        print(f"  State: {stats['state']}")
        
        print("✅ Test 1 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
        return False

def test_auto_simulator():
    """Test 2: Automatic simulator with callbacks"""
    print("\n" + "=" * 50)
    print("TEST 2: Automatic Live Simulator")
    print("=" * 50)
    
    try:
        simulator = LiveMarketSimulator(
            total_points=100,
            initial_price=45,
            volatility=1.5,
            save_to_csv=True
        )
        
        # Add a callback to track price changes
        price_updates = []
        
        def price_tracker(data_point):
            price_updates.append(data_point['price'])
            print(f"  Price update: ${data_point['price']:.2f} "
                  f"(Point {data_point['point_index']}/{simulator.total_points})")
        
        simulator.add_price_update_callback(price_tracker)
        
        # Start automatic simulation
        print("Starting automatic simulation (0.2 second intervals)...")
        simulator.start_live_simulation(time_interval=0.2, mode="auto")
        
        # Let it run for a bit
        time.sleep(6)  # 6 seconds = about 30 data points
        
        # Pause and check progress
        simulator.pause()
        stats = simulator.get_simulation_stats()
        print(f"\nPaused simulation:")
        print(f"  Generated {len(price_updates)} price updates")
        if price_updates:
            print(f"  Price range: ${min(price_updates):.2f} - ${max(price_updates):.2f}")
        print(f"  Current price: ${stats['current_price']:.2f}")
        
        # Resume briefly
        print("\nResuming for 2 more seconds...")
        simulator.resume()
        time.sleep(2)
        
        # Stop simulation
        simulator.stop()
        
        # Final stats
        final_stats = simulator.get_simulation_stats()
        print(f"\nFinal results:")
        print(f"  Total points generated: {len(simulator.data_history)}")
        print(f"  Final price: ${final_stats['current_price']:.2f}")
        if simulator.csv_filename:
            print(f"  CSV saved to: data/market_data/{simulator.csv_filename}")
        
        print("✅ Test 2 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}")
        return False

def test_portfolio_integration():
    """Test 3: Integration with portfolio system"""
    print("\n" + "=" * 50)
    print("TEST 3: Portfolio Integration")
    print("=" * 50)
    
    try:
        # Create components
        simulator = LiveMarketSimulator(
            total_points=40,
            initial_price=52,
            volatility=1.8,
            save_to_csv=False  # Don't save for this test
        )
        
        # Create portfolio manager
        portfolio_manager = PortfolioManager(db_path="data/databases/test_trading.db")
        portfolio_manager.clear_database()  # Fresh start
        
        # Create test user
        user_id = portfolio_manager.create_user("TestTrader", 10000)
        
        # Set up integration
        integrator = PortfolioIntegrator(simulator, portfolio_manager)
        
        print("Created portfolio integration:")
        print(f"  Test user: TestTrader with $10,000")
        print(f"  Portfolio will auto-update with market data")
        
        # Start simulation
        print(f"\nStarting integrated simulation...")
        simulator.start_live_simulation(time_interval=0.3, mode="auto")
        
        # Let it run to build up some data
        time.sleep(3)
        
        # Execute some test trades
        print(f"\nExecuting test trades...")
        
        # Buy some contracts
        success, msg = portfolio_manager.execute_trade(user_id, 0.5, 5, TradeType.BUY)
        print(f"  Trade 1 (Buy 5 @ 0.5): {msg}")
        
        # Let market move a bit
        time.sleep(2)
        
        # Buy more at different strike
        success, msg = portfolio_manager.execute_trade(user_id, 0.6, 3, TradeType.BUY)
        print(f"  Trade 2 (Buy 3 @ 0.6): {msg}")
        
        # Let market move more
        time.sleep(2)
        
        # Sell some
        success, msg = portfolio_manager.execute_trade(user_id, 0.5, 2, TradeType.SELL)
        print(f"  Trade 3 (Sell 2 @ 0.5): {msg}")
        
        # Stop simulation
        simulator.stop()
        
        # Show final portfolio
        portfolio = portfolio_manager.get_user_portfolio(user_id)
        print(f"\nFinal Portfolio:")
        print(f"  Cash: ${portfolio['cash']:,.2f}")
        print(f"  Position Value: ${portfolio['total_position_value']:,.2f}")
        print(f"  Total Portfolio: ${portfolio['total_portfolio_value']:,.2f}")
        print(f"  Unrealized P&L: ${portfolio['total_unrealized_pnl']:,.2f}")
        
        for pos in portfolio['positions']:
            print(f"  Strike {pos['strike']}: {pos['quantity']} contracts @ "
                  f"${pos['current_price']:.4f} current")
        
        # Get integration stats
        integration_stats = integrator.get_integration_stats()
        print(f"\nIntegration Stats:")
        print(f"  Portfolio updates: {integration_stats['total_updates']}")
        print(f"  Final market price: ${integration_stats['current_market_price']:.2f}")
        
        print("✅ Test 3 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}")
        return False

def test_data_analysis():
    """Test 4: Data analysis features"""
    print("\n" + "=" * 50)
    print("TEST 4: Data Analysis Features")
    print("=" * 50)
    
    try:
        # Create simulator and generate some data
        simulator = LiveMarketSimulator(
            total_points=50,
            initial_price=48,
            save_to_csv=False
        )
        
        # Generate data quickly
        print("Generating sample data...")
        simulator.start_live_simulation(time_interval=0.05, mode="auto")  # Very fast
        time.sleep(3)  # Should generate most points
        simulator.stop()
        
        # Test data analysis features
        print(f"\nData Analysis Features:")
        
        # Full history
        full_df = simulator.get_full_history_df()
        print(f"  Full history: {len(full_df)} data points")
        
        # Recent window
        recent = simulator.get_recent_history(10)
        if recent:
            recent_prices = [d['price'] for d in recent]
            print(f"  Recent 10 prices: {[f'${p:.2f}' for p in recent_prices]}")
        
        # Show data ready for charting
        if len(simulator.data_history) >= 10:
            chart_data = {
                'labels': [d['timestamp'].strftime('%H:%M:%S') for d in simulator.data_history[-10:]],
                'prices': [d['price'] for d in simulator.data_history[-10:]],
                'volumes': [d['volume'] for d in simulator.data_history[-10:]]
            }
            
            print(f"\nChart-ready data (last 10 points):")
            print(f"  Times: {chart_data['labels']}")
            print(f"  Prices: {chart_data['prices']}")
        
        print("✅ Test 4 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Test 4 FAILED: {e}")
        return False

def main():
    """Run all tests"""
    print("LIVE MARKET SIMULATOR TESTING")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_results.append(test_basic_simulator())
    test_results.append(test_auto_simulator())
    test_results.append(test_portfolio_integration())
    test_results.append(test_data_analysis())
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 60)
    if passed == total:
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("Your live market simulator is working perfectly!")
        print("\nNext steps:")
        print("1. Try modifying the simulation parameters")
        print("2. Create your own trading strategies")
        print("3. Build real-time charts")
        print("4. Develop the FastAPI backend")
        return True
    else:
        print(f"TESTS COMPLETED: {passed}/{total} PASSED")
        print("=" * 60)
        print("Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n✅ All tests passed! Your system is ready to use.")
    else:
        print(f"\n❌ Some tests failed. Please check the errors above.")
    
    input("\nPress Enter to exit...")