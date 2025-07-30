import random
import numpy as np
import pandas as pd
import os
from datetime import datetime, timedelta
import math

class PredictionMarketSimulator:
    def __init__(self, 
                 total_points=1500, 
                 initial_price=50, 
                 volatility=1.8,
                 threshold_percentage=0.7,
                 trend_strength=0.08,
                 max_movement=4.0):
        """
        Initialize the prediction market simulator
        
        Args:
            total_points (int): Total number of data points to generate
            initial_price (float): Starting price (typically around 50 for balanced market)
            volatility (float): Base volatility for random movements
            threshold_percentage (float): At what percentage of total points to start trending
            trend_strength (float): How strong the trend toward resolution should be
            max_movement (float): Maximum price movement per step in percentage points
        """
        self.total_points = total_points
        self.initial_price = max(15, min(85, initial_price))  # Keep away from extreme bounds
        self.volatility = volatility
        self.threshold_point = int(total_points * threshold_percentage)
        self.trend_strength = trend_strength
        self.max_movement = max_movement
        
        # Randomly determine final resolution (True = YES, False = NO)
        self.final_resolution = random.choice([True, False])
        self.target_price = 95 if self.final_resolution else 5
        
        print(f"Market will resolve to: {'YES' if self.final_resolution else 'NO'}")
        print(f"Trending will begin after point {self.threshold_point}")
        print(f"Max movement per step: {self.max_movement}%")

    def apply_soft_bounds(self, price: float, movement: float, is_pre_threshold: bool) -> float:
        """Apply soft bounds that gently discourage extreme values"""
        
        if is_pre_threshold:
            comfort_zone = (12.0, 88.0)  # Prefer to stay in this range
            warning_zone = (8.0, 92.0)   # Start gentle pushback here
        else:
            comfort_zone = (5.0, 95.0)   # Wider range post-threshold
            warning_zone = (2.0, 98.0)   # Gentle bounds
        
        new_price = price + movement
        
        # Only apply soft dampening if we're getting near warning zones
        if new_price < warning_zone[0]:
            # Gentle pushback when getting too low
            if new_price < comfort_zone[0]:
                distance_below = comfort_zone[0] - new_price
                dampening_factor = min(0.6, distance_below * 0.1)  # Maximum 60% dampening
                adjusted_movement = movement * (1 - dampening_factor)
                new_price = price + adjusted_movement
            
        elif new_price > warning_zone[1]:
            # Gentle pushback when getting too high
            if new_price > comfort_zone[1]:
                distance_above = new_price - comfort_zone[1]
                dampening_factor = min(0.6, distance_above * 0.1)  # Maximum 60% dampening
                adjusted_movement = movement * (1 - dampening_factor)
                new_price = price + adjusted_movement
        
        # Hard safety bounds (should rarely be needed)
        if is_pre_threshold:
            new_price = max(5.0, min(95.0, new_price))
        else:
            new_price = max(1.0, min(99.0, new_price))
            
        return new_price

    def generate_price_movement(self, current_price: float, point_index: int, previous_movement: float = 0.0) -> float:
        """Generate the next price movement with realistic constraints"""
        
        # Calculate distance to target and remaining points
        remaining_points = self.total_points - point_index
        is_pre_threshold = point_index < self.threshold_point
        
        if is_pre_threshold:
            # Pre-threshold: primarily random movement with light momentum
            momentum_factor = 0.2 * previous_movement
            random_component = np.random.normal(0, self.volatility)
            
            # Very weak signal toward eventual resolution (barely noticeable)
            weak_signal = 0.01 * (self.target_price - current_price) / 100
            
            movement = momentum_factor + random_component + weak_signal
            
        else:
            # Post-threshold: add directional bias but keep volatility high
            distance_to_target = self.target_price - current_price
            
            # Gradual trend that starts weak and slowly increases
            trend_progress = (point_index - self.threshold_point) / (self.total_points - self.threshold_point)
            
            # Much more gradual trending - starts at 10% strength, slowly increases
            base_trend = self.trend_strength * distance_to_target / 100
            progressive_trend = base_trend * (0.1 + 0.9 * trend_progress)
            
            # Keep substantial random movement even after threshold
            volatility_factor = 0.75 + 0.25 * (remaining_points / (self.total_points - self.threshold_point))
            current_volatility = self.volatility * volatility_factor
            
            random_component = np.random.normal(0, current_volatility)
            momentum_factor = 0.15 * previous_movement
            
            movement = progressive_trend + random_component + momentum_factor
        
        # Apply movement cap but make it much less restrictive
        movement = max(-self.max_movement, min(self.max_movement, movement))
        
        return movement

    def generate_market_data(self):
        """Generate the complete market data series
        
        Uses soft bounds that dampen movement near limits rather than hard clipping:
        - Pre-threshold: naturally stays within ~[9%, 90%] via soft dampening
        - Post-threshold: gradually expands range but still prevents extreme jumps
        - Movement size is capped to simulate liquid market behavior
        """
        prices: list[float] = [float(self.initial_price)]
        movements: list[float] = [0.0]
        timestamps: list[datetime] = []
        
        # Generate timestamps (every 5 minutes for realistic market data)
        start_time = datetime.now() - timedelta(minutes=5 * self.total_points)
        
        for i in range(self.total_points):
            timestamp = start_time + timedelta(minutes=5 * i)
            timestamps.append(timestamp)
            
            if i > 0:
                previous_movement = movements[-1] if len(movements) > 1 else 0.0
                movement = self.generate_price_movement(prices[-1], i, previous_movement)
                movements.append(float(movement))
                
                # Apply soft bounds instead of hard clipping
                is_pre_threshold = i < self.threshold_point
                new_price = self.apply_soft_bounds(prices[-1], movement, is_pre_threshold)
                
                prices.append(float(new_price))
        
        # Ensure final price trends toward resolution value but don't force it completely
        if len(prices) > 0:
            final_adjustment = float(self.target_price) - prices[-1]
            # Only adjust 40% of the way there to keep it realistic
            adjusted_price = prices[-1] + final_adjustment * 0.4
            prices[-1] = max(2.0, min(98.0, adjusted_price))
        
        return timestamps, prices, movements

    def create_csv_data(self):
        """Create structured data for CSV export"""
        timestamps, prices, movements = self.generate_market_data()
        
        # Calculate additional market metrics
        volumes: list[int] = []
        bid_ask_spreads: list[float] = []
        
        for i, price in enumerate(prices):
            # Simulate volume (higher volume around significant price movements)
            base_volume = random.randint(50, 200)
            movement_factor = abs(movements[i]) if i < len(movements) else 0.0
            volume_multiplier = 1.0 + float(movement_factor) * 0.5
            volume = int(float(base_volume) * volume_multiplier)
            volumes.append(volume)
            
            # Simulate bid-ask spread (tighter spreads for more liquid markets)
            base_spread = 0.5 + random.uniform(-0.2, 0.2)
            # Wider spreads when price is more volatile
            volatility_factor = float(movement_factor) * 0.1
            spread = max(0.1, base_spread + volatility_factor)
            bid_ask_spreads.append(round(spread, 2))
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': timestamps,
            'price': [round(float(p), 2) for p in prices],
            'movement': [round(float(m), 3) for m in movements],
            'volume': volumes,
            'bid_ask_spread': bid_ask_spreads,
            'market_resolution': [self.final_resolution] * len(timestamps)
        })
        
        return df

def save_to_csv(df, filename=None):
    """Save DataFrame to CSV in a data folder"""
    
    # Create data directory if it doesn't exist
    data_dir = "market_data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory: {data_dir}")
    
    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        resolution = "YES" if df['market_resolution'].iloc[0] else "NO"
        filename = f"prediction_market_{resolution}_{timestamp}.csv"
    
    filepath = os.path.join(data_dir, filename)
    
    # Save to CSV
    df.to_csv(filepath, index=False)
    print(f"Market data saved to: {filepath}")
    print(f"Generated {len(df)} data points")
    print(f"Price range: {df['price'].min():.2f} - {df['price'].max():.2f}")
    print(f"Final price: {df['price'].iloc[-1]:.2f}")
    
    return filepath

def main():
    """Main function to run the simulation"""
    print("🎯 Prediction Market Data Generator")
    print("=" * 40)
    
    # Create simulator with customizable parameters
    simulator = PredictionMarketSimulator(
        total_points=1500,       # Number of data points (as intended)
        initial_price=50,        # Starting price (50 = neutral)
        volatility=1.65,          # Realistic volatility for 1500-point dataset
        threshold_percentage=0.8, # Start trending at 70% through the data (point 1050)
        trend_strength=0.085,     # Very gradual trending for long dataset
        max_movement=3.0         # Max 3% movement per step - realistic but not restrictive
    )
    
    # Generate market data
    print("\nGenerating market data...")
    market_data = simulator.create_csv_data()
    
    # Save to CSV
    filepath = save_to_csv(market_data)
    
    # Display summary statistics
    print("\n📊 Summary Statistics:")
    print(f"Market Resolution: {'YES' if simulator.final_resolution else 'NO'}")
    print(f"Average Price: {market_data['price'].mean():.2f}")
    print(f"Price Volatility (std): {market_data['price'].std():.2f}")
    print(f"Total Volume: {market_data['volume'].sum():,}")
    print(f"Average Spread: {market_data['bid_ask_spread'].mean():.2f}")
    
    return filepath

if __name__ == "__main__":
    # Run multiple simulations if desired
    print("Generating prediction market simulation...")
    
    try:
        filepath = main()
        print(f"\n✅ Simulation complete! Data saved to: {filepath}")
        
        # Ask if user wants to generate another simulation
        response = input("\nGenerate another simulation? (y/n): ").lower().strip()
        while response == 'y':
            print("\n" + "="*50)
            filepath = main()
            print(f"\n✅ Additional simulation complete! Data saved to: {filepath}")
            response = input("\nGenerate another simulation? (y/n): ").lower().strip()
            
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        print("Please check your Python environment and try again.")