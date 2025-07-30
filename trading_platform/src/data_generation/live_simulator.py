import threading
import time
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import os
import csv

class SimulationState(Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING" 
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"

class LiveMarketSimulator:
    """
    Real-time streaming version of the prediction market simulator.
    Generates data points one at a time with configurable time intervals.
    """
    
    def __init__(self, 
                 total_points: int = 1500,
                 initial_price: float = 50,
                 volatility: float = 1.8,
                 threshold_percentage: float = 0.7,
                 trend_strength: float = 0.08,
                 max_movement: float = 4.0,
                 save_to_csv: bool = True,
                 csv_filename: Optional[str] = None):
        """
        Initialize the live market simulator
        """
        # Simulation parameters
        self.total_points = total_points
        self.initial_price = max(15, min(85, initial_price))
        self.volatility = volatility
        self.threshold_point = int(total_points * threshold_percentage)
        self.trend_strength = trend_strength
        self.max_movement = max_movement
        
        # Market resolution
        self.final_resolution = random.choice([True, False])
        self.target_price = 95 if self.final_resolution else 5
        
        # Current simulation state
        self.current_point_index = 0
        self.current_price = float(self.initial_price)
        self.previous_movement = 0.0
        self.simulation_state = SimulationState.STOPPED
        
        # Data storage
        self.data_history: List[Dict[str, Any]] = []
        self.current_data_point: Optional[Dict[str, Any]] = None
        
        # Threading
        self.simulation_thread: Optional[threading.Thread] = None
        self.time_interval = 1.0  # Default 1 second
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        
        # CSV handling
        self.save_to_csv = save_to_csv
        self.csv_filename = csv_filename
        self.csv_file: Optional[Any] = None
        self.csv_writer: Optional[Any] = None
        
        # Callbacks for integration
        self.price_update_callbacks: List[Callable] = []
        
        # Start time for realistic timestamps
        self.start_time = datetime.now()
        
        print(f"Live Market Simulator Initialized")
        print(f"Market will resolve to: {'YES' if self.final_resolution else 'NO'}")
        print(f"Trending will begin after point {self.threshold_point}")
        print(f"Total points to generate: {self.total_points}")

    def add_price_update_callback(self, callback: Callable) -> None:
        """Add a callback function that gets called when price updates."""
        self.price_update_callbacks.append(callback)
    
    def remove_price_update_callback(self, callback: Callable) -> None:
        """Remove a previously added callback"""
        if callback in self.price_update_callbacks:
            self.price_update_callbacks.remove(callback)
    
    def _setup_csv_file(self) -> None:
        """Setup CSV file for incremental writing"""
        if not self.save_to_csv:
            return
            
        # Create data directory if it doesn't exist
        data_dir = "data/market_data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Generate distinguishable filename if not provided
        if self.csv_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            resolution = "YES" if self.final_resolution else "NO"
            self.csv_filename = f"LIVE_market_{resolution}_{timestamp}_T{self.total_points}.csv"
        
        filepath = os.path.join(data_dir, self.csv_filename)
        
        # Open CSV file and write header
        self.csv_file = open(filepath, 'w', newline='')
        fieldnames = ['timestamp', 'price', 'movement', 'volume', 'bid_ask_spread', 'market_resolution']
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=fieldnames)
        self.csv_writer.writeheader()
        if self.csv_file:
            self.csv_file.flush()
        
        print(f"CSV file created: {filepath}")
    
    def _close_csv_file(self) -> None:
        """Close CSV file"""
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None
    
    def apply_soft_bounds(self, price: float, movement: float, is_pre_threshold: bool) -> float:
        """Apply soft bounds that gently discourage extreme values"""
        
        if is_pre_threshold:
            comfort_zone = (12.0, 88.0)
            warning_zone = (8.0, 92.0)
        else:
            comfort_zone = (5.0, 95.0)
            warning_zone = (2.0, 98.0)
        
        new_price = price + movement
        
        if new_price < warning_zone[0]:
            if new_price < comfort_zone[0]:
                distance_below = comfort_zone[0] - new_price
                dampening_factor = min(0.6, distance_below * 0.1)
                adjusted_movement = movement * (1 - dampening_factor)
                new_price = price + adjusted_movement
                
        elif new_price > warning_zone[1]:
            if new_price > comfort_zone[1]:
                distance_above = new_price - comfort_zone[1]
                dampening_factor = min(0.6, distance_above * 0.1)
                adjusted_movement = movement * (1 - dampening_factor)
                new_price = price + adjusted_movement
        
        if is_pre_threshold:
            new_price = max(5.0, min(95.0, new_price))
        else:
            new_price = max(1.0, min(99.0, new_price))
            
        return new_price

    def generate_price_movement(self, current_price: float, point_index: int, previous_movement: float = 0.0) -> float:
        """Generate the next price movement"""
        
        remaining_points = self.total_points - point_index
        is_pre_threshold = point_index < self.threshold_point
        
        if is_pre_threshold:
            momentum_factor = 0.2 * previous_movement
            random_component = np.random.normal(0, self.volatility)
            weak_signal = 0.01 * (self.target_price - current_price) / 100
            movement = momentum_factor + random_component + weak_signal
            
        else:
            distance_to_target = self.target_price - current_price
            trend_progress = (point_index - self.threshold_point) / (self.total_points - self.threshold_point)
            base_trend = self.trend_strength * distance_to_target / 100
            progressive_trend = base_trend * (0.1 + 0.9 * trend_progress)
            
            volatility_factor = 0.75 + 0.25 * (remaining_points / (self.total_points - self.threshold_point))
            current_volatility = self.volatility * volatility_factor
            
            random_component = np.random.normal(0, current_volatility)
            momentum_factor = 0.15 * previous_movement
            
            movement = progressive_trend + random_component + momentum_factor
        
        movement = max(-self.max_movement, min(self.max_movement, movement))
        return movement

    def generate_next_data_point(self) -> Optional[Dict[str, Any]]:
        """
        Generate the next single data point in the simulation.
        Returns a dictionary with the data point information, or None if complete.
        """
        if self.current_point_index >= self.total_points:
            self.simulation_state = SimulationState.COMPLETED
            return None
        
        # Generate timestamp
        timestamp = self.start_time + timedelta(minutes=5 * self.current_point_index)
        
        # Generate price movement (except for first point)
        if self.current_point_index > 0:
            movement = self.generate_price_movement(
                self.current_price, 
                self.current_point_index, 
                self.previous_movement
            )
            
            # Apply soft bounds
            is_pre_threshold = self.current_point_index < self.threshold_point
            new_price = self.apply_soft_bounds(self.current_price, movement, is_pre_threshold)
            
            self.current_price = new_price
            self.previous_movement = movement
        else:
            movement = 0.0
        
        # Generate volume
        base_volume = random.randint(50, 200)
        movement_factor = abs(movement)
        volume_multiplier = 1.0 + float(movement_factor) * 0.5
        volume = int(float(base_volume) * volume_multiplier)
        
        # Generate bid-ask spread
        base_spread = 0.5 + random.uniform(-0.2, 0.2)
        volatility_factor = float(movement_factor) * 0.1
        spread = max(0.1, base_spread + volatility_factor)
        
        # Create data point
        data_point: Dict[str, Any] = {
            'timestamp': timestamp,
            'price': round(float(self.current_price), 2),
            'movement': round(float(movement), 3),
            'volume': volume,
            'bid_ask_spread': round(spread, 2),
            'market_resolution': self.final_resolution,
            'point_index': self.current_point_index
        }
        
        # Store in history
        self.data_history.append(data_point)
        self.current_data_point = data_point
        
        # Save to CSV if enabled
        if self.save_to_csv and self.csv_writer:
            csv_row = {k: v for k, v in data_point.items() if k != 'point_index'}
            self.csv_writer.writerow(csv_row)
            if self.csv_file:
                self.csv_file.flush()
        
        # Call callbacks
        for callback in self.price_update_callbacks:
            try:
                callback(data_point.copy())
            except Exception as e:
                print(f"Error in callback: {e}")
        
        # Increment counter
        self.current_point_index += 1
        
        return data_point

    def step(self) -> Optional[Dict[str, Any]]:
        """Manual step: generate the next data point."""
        return self.generate_next_data_point()

    def start_live_simulation(self, time_interval: float = 1.0, mode: str = "auto") -> None:
        """Start the live simulation in either automatic or manual mode."""
        if self.simulation_state == SimulationState.RUNNING:
            print("Simulation already running!")
            return
        
        self.time_interval = time_interval
        self.simulation_state = SimulationState.RUNNING
        self._stop_event.clear()
        self._pause_event.clear()
        
        # Setup CSV if needed
        if self.save_to_csv:
            self._setup_csv_file()
        
        if mode == "auto":
            # Start simulation thread
            self.simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
            self.simulation_thread.start()
            print(f"Live simulation started in AUTO mode (interval: {time_interval}s)")
        else:
            print(f"Live simulation started in MANUAL mode (call step() to advance)")
            self.simulation_state = SimulationState.PAUSED

    def _simulation_loop(self) -> None:
        """Main simulation loop that runs in background thread"""
        while (not self._stop_event.is_set() and 
               self.current_point_index < self.total_points and
               self.simulation_state != SimulationState.COMPLETED):
            
            # Check if paused
            if self._pause_event.is_set():
                time.sleep(0.1)
                continue
            
            # Generate next data point
            data_point = self.generate_next_data_point()
            
            if data_point is None:
                break
                
            # Wait for time interval
            if not self._stop_event.wait(self.time_interval):
                continue
            else:
                break
        
        # Simulation finished
        if self.current_point_index >= self.total_points:
            self.simulation_state = SimulationState.COMPLETED
            print("Simulation completed!")
        else:
            self.simulation_state = SimulationState.STOPPED
            print("Simulation stopped")
        
        # Final price adjustment
        if len(self.data_history) > 0:
            final_adjustment = float(self.target_price) - self.current_price
            adjusted_price = self.current_price + final_adjustment * 0.4
            self.current_price = max(2.0, min(98.0, adjusted_price))
            
            # Update last data point safely
            if self.data_history:
                self.data_history[-1]['price'] = round(self.current_price, 2)
            if self.current_data_point:
                self.current_data_point['price'] = round(self.current_price, 2)
        
        self._close_csv_file()

    def pause(self) -> None:
        """Pause the live simulation"""
        if self.simulation_state == SimulationState.RUNNING:
            self._pause_event.set()
            self.simulation_state = SimulationState.PAUSED
            print("Simulation paused")

    def resume(self) -> None:
        """Resume the paused simulation"""
        if self.simulation_state == SimulationState.PAUSED:
            self._pause_event.clear()
            self.simulation_state = SimulationState.RUNNING
            print("Simulation resumed")

    def stop(self) -> None:
        """Stop the live simulation"""
        if self.simulation_state in [SimulationState.RUNNING, SimulationState.PAUSED]:
            self._stop_event.set()
            self._pause_event.clear()
            
            if self.simulation_thread and self.simulation_thread.is_alive():
                self.simulation_thread.join(timeout=2.0)
            
            self.simulation_state = SimulationState.STOPPED
            self._close_csv_file()
            print("Simulation stopped")

    def get_current_price(self) -> float:
        """Get the current market price"""
        return self.current_price

    def get_current_data_point(self) -> Optional[Dict[str, Any]]:
        """Get the current data point"""
        return self.current_data_point.copy() if self.current_data_point else None

    def get_recent_history(self, n_points: int = 100) -> List[Dict[str, Any]]:
        """Get the most recent N data points"""
        return self.data_history[-n_points:] if self.data_history else []

    def get_full_history_df(self) -> pd.DataFrame:
        """Get all historical data as a pandas DataFrame"""
        if not self.data_history:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.data_history)
        if 'point_index' in df.columns:
            df = df.drop('point_index', axis=1)
        return df

    def get_simulation_stats(self) -> Dict[str, Any]:
        """Get current simulation statistics"""
        return {
            'state': self.simulation_state.value,
            'current_point': self.current_point_index,
            'total_points': self.total_points,
            'progress_percent': (self.current_point_index / self.total_points) * 100,
            'current_price': self.current_price,
            'target_resolution': 'YES' if self.final_resolution else 'NO',
            'is_trending': self.current_point_index >= self.threshold_point,
            'time_interval': self.time_interval
        }

    def reset_simulation(self) -> None:
        """Reset simulation to beginning"""
        self.stop()
        
        # Reset state
        self.current_point_index = 0
        self.current_price = float(self.initial_price)
        self.previous_movement = 0.0
        self.simulation_state = SimulationState.STOPPED
        
        # Clear data
        self.data_history.clear()
        self.current_data_point = None
        
        # Reset timing
        self.start_time = datetime.now()
        
        print("Simulation reset to beginning")


# Integration helper for portfolio management
class PortfolioIntegrator:
    """
    Helper class to integrate LiveMarketSimulator with PortfolioManager.
    """
    
    def __init__(self, simulator: LiveMarketSimulator, portfolio_manager: Any):
        self.simulator = simulator
        self.portfolio_manager = portfolio_manager
        self.update_count = 0
        
        # Register callback to update portfolio on price changes
        self.simulator.add_price_update_callback(self.on_price_update)
        
        print("Portfolio integration enabled")
    
    def on_price_update(self, data_point: Dict[str, Any]) -> None:
        """Called when simulator generates a new data point."""
        try:
            # Convert single data point to DataFrame format
            df = pd.DataFrame([{
                'timestamp': data_point['timestamp'],
                'price': data_point['price'],
                'volume': data_point['volume']
            }])
            
            # Update portfolio manager with new market data
            self.portfolio_manager.update_market_data(df)
            self.update_count += 1
            
            # Log periodic updates
            if self.update_count % 25 == 0:
                print(f"Portfolio updated ({self.update_count} total updates) - "
                      f"Market price: ${data_point['price']:.2f}")
                
        except Exception as e:
            print(f"Error updating portfolio: {e}")
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get statistics about the integration"""
        return {
            'total_updates': self.update_count,
            'current_market_price': self.simulator.get_current_price(),
        }