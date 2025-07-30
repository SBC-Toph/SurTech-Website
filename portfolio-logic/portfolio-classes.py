import pandas as pd
import numpy as np
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Import your existing pricing function
# from price_logic import compute_option_prices_from_df

class TradeType(Enum):
    BUY = "BUY"
    SELL = "SELL"

class PositionStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    SETTLED = "SETTLED"

@dataclass
class Trade:
    """Represents a single trade transaction"""
    trade_id: str
    user_id: str
    timestamp: datetime
    trade_type: TradeType
    strike_price: float
    quantity: int
    price_per_contract: float
    total_cost: float
    market_price_at_trade: float  # Underlying market price when trade was made
    
class Position:
    """Represents a user's position in a specific option contract"""
    def __init__(self, user_id: str, strike_price: float):
        self.user_id = user_id
        self.strike_price = strike_price
        self.quantity = 0  # Net quantity (positive = long, negative = short)
        self.total_cost_basis = 0.0  # Total money invested
        self.trades: List[Trade] = []
        self.status = PositionStatus.OPEN
        self.settlement_value = 0.0
    
    def add_trade(self, trade: Trade):
        """Add a trade to this position and update quantities/cost basis"""
        self.trades.append(trade)
        
        if trade.trade_type == TradeType.BUY:
            self.quantity += trade.quantity
            self.total_cost_basis += trade.total_cost
        else:  # SELL
            self.quantity -= trade.quantity
            self.total_cost_basis -= trade.total_cost
    
    def get_average_cost_per_contract(self) -> float:
        """Calculate average cost per contract for this position"""
        if self.quantity == 0:
            return 0.0
        return self.total_cost_basis / abs(self.quantity)
    
    def calculate_unrealized_pnl(self, current_option_price: float) -> float:
        """Calculate unrealized P&L based on current market price"""
        if self.status != PositionStatus.OPEN:
            return 0.0
        
        current_market_value = self.quantity * current_option_price
        return current_market_value - self.total_cost_basis
    
    def settle_position(self, final_market_price: float, strike_price: float) -> float:
        """Settle the position when market resolves (call option payoff)"""
        if self.status != PositionStatus.OPEN:
            return self.settlement_value
        
        # Call option payoff: max(S - K, 0) where S = final price, K = strike
        # Convert market price from percentage to decimal (e.g., 75 -> 0.75)
        final_price_decimal = final_market_price / 100
        option_payoff = max(final_price_decimal - strike_price, 0)
        
        self.settlement_value = self.quantity * option_payoff
        self.status = PositionStatus.SETTLED
        
        return self.settlement_value

class PortfolioManager:
    """Main class that manages user portfolios and trading"""
    
    def __init__(self, db_path: str = "trading_platform.db"):
        self.db_path = db_path
        self.users: Dict[str, Dict] = {}  # user_id -> user data
        self.positions: Dict[str, Dict[float, Position]] = {}  # user_id -> {strike -> Position}
        self.current_market_data: Optional[pd.DataFrame] = None
        self.current_option_prices: Optional[pd.DataFrame] = None
        self.market_resolved = False
        self.final_market_price = None
        
        # Initialize database
        self._init_database()
        
        # Load existing users from database
        self._load_all_users_from_db()
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                starting_cash REAL NOT NULL,
                current_cash REAL NOT NULL,
                total_realized_pnl REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                trade_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                trade_type TEXT NOT NULL,
                strike_price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                price_per_contract REAL NOT NULL,
                total_cost REAL NOT NULL,
                market_price_at_trade REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Positions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                position_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                strike_price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                total_cost_basis REAL NOT NULL,
                status TEXT NOT NULL,
                settlement_value REAL DEFAULT 0.0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized at: {self.db_path}")
    
    def _load_all_users_from_db(self):
        """Load all existing users from database into memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        user_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        for user_id in user_ids:
            self.load_user_from_db(user_id)
    
    def create_user(self, username: str, starting_cash: float = 15000.0) -> str:
        """Create a new user with starting cash"""
        # Check if user already exists
        existing_user = self.get_user_by_username(username)
        if existing_user:
            user_id = existing_user['user_id']
            # Make sure user is loaded in memory
            if user_id not in self.users:
                self.load_user_from_db(user_id)
            print(f"⚠️  User '{username}' already exists, loading existing account")
            return user_id
        
        user_id = str(uuid.uuid4())
        
        # Add to in-memory storage
        self.users[user_id] = {
            'username': username,
            'starting_cash': starting_cash,
            'current_cash': starting_cash,
            'total_realized_pnl': 0.0
        }
        self.positions[user_id] = {}
        
        # Add to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (user_id, username, starting_cash, current_cash)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, starting_cash, starting_cash))
        conn.commit()
        conn.close()
        
        print(f"✅ Created user '{username}' with ${starting_cash:,.2f} starting cash")
        return user_id
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM users WHERE username = ?
        ''', (username,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'user_id': result[0],
                'username': result[1],
                'starting_cash': result[2],
                'current_cash': result[3],
                'total_realized_pnl': result[4]
            }
        return None
    
    def load_user_from_db(self, user_id: str):
        """Load user and their positions from database into memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load user data
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user_result = cursor.fetchone()
        if not user_result:
            conn.close()
            return False
        
        self.users[user_id] = {
            'username': user_result[1],
            'starting_cash': user_result[2],
            'current_cash': user_result[3],
            'total_realized_pnl': user_result[4]
        }
        
        # Load user's trades and rebuild positions
        self.positions[user_id] = {}
        cursor.execute('''
            SELECT * FROM trades WHERE user_id = ? ORDER BY timestamp
        ''', (user_id,))
        trades = cursor.fetchall()
        
        for trade_row in trades:
            strike_price = trade_row[4]
            if strike_price not in self.positions[user_id]:
                self.positions[user_id][strike_price] = Position(user_id, strike_price)
            
            # Reconstruct trade object
            trade = Trade(
                trade_id=trade_row[0],
                user_id=trade_row[1],
                timestamp=datetime.fromisoformat(trade_row[2]),
                trade_type=TradeType(trade_row[3]),
                strike_price=trade_row[4],
                quantity=trade_row[5],
                price_per_contract=trade_row[6],
                total_cost=trade_row[7],
                market_price_at_trade=trade_row[8]
            )
            
            self.positions[user_id][strike_price].add_trade(trade)
        
        conn.close()
        return True
    
    def clear_database(self):
        """Clear all data from database (useful for testing)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM trades')
        cursor.execute('DELETE FROM positions')  
        cursor.execute('DELETE FROM users')
        conn.commit()
        conn.close()
        
        self.users.clear()
        self.positions.clear()
        print("🗑️  Database cleared")
    
    def update_market_data(self, market_df: pd.DataFrame):
        """Update current market data and recalculate option prices"""
        self.current_market_data = market_df.copy()
        
        # Use your pricing function to calculate option prices for multiple strikes
        strikes = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]  # Common strike prices
        
        # Convert market prices to yes/no probabilities
        # Assuming your market_df has a 'price' column with values 0-100
        latest_price = market_df['price'].iloc[-1]
        yes_prob = latest_price / 100
        no_prob = 1 - yes_prob
        
        # Create a simple DataFrame for pricing (using latest market data point)
        pricing_df = pd.DataFrame({
            'yes_price': [yes_prob],
            'no_price': [no_prob]
        })
        
        # Calculate option prices for each strike
        option_data = []
        for strike in strikes:
            # This calls your existing function
            option_df = self.compute_option_prices_from_df(pricing_df, strike_price=strike)
            bid_price = option_df['option_bid'].iloc[0]
            ask_price = option_df['option_ask'].iloc[0]
            
            option_data.append({
                'strike': strike,
                'bid': bid_price,
                'ask': ask_price,
                'mid': (bid_price + ask_price) / 2
            })
        
        self.current_option_prices = pd.DataFrame(option_data)
        
        # Debug output
        print(f"📊 Updated market data. Current price: {latest_price:.2f}")
        print(f"    Yes prob: {yes_prob:.3f}, No prob: {no_prob:.3f}")
        if len(option_data) > 0:
            print(f"    Sample option price (strike 0.5): Bid={option_data[2]['bid']:.4f}, Ask={option_data[2]['ask']:.4f}")
    
    def compute_option_prices_from_df(self, df: pd.DataFrame, strike_price: float = 0.5, 
                                    decay_rate: float = 1.5, yes_col: str = 'yes_price', 
                                    no_col: str = 'no_price') -> pd.DataFrame:
        """
        Your existing pricing function - modified to handle single-row DataFrames
        """
        df = df.copy()
        T = len(df) - 1
        df['t_index'] = range(len(df))
        
        # Handle case where T = 0 (single row)
        if T == 0:
            df['decay_multiplier'] = 1.0  # No decay for single point
        else:
            df['decay_multiplier'] = np.exp(-decay_rate * (df['t_index'].to_numpy() / T))
        
        df['option_bid'] = df[yes_col] * (1 - strike_price) * df['decay_multiplier']
        df['option_ask'] = (1 - df[no_col]) * (1 - strike_price) * df['decay_multiplier']
        
        return df
    
    def get_option_price(self, strike_price: float, side: str = "mid") -> float:
        """Get current option price for a given strike"""
        if self.current_option_prices is None:
            raise ValueError("No market data available. Call update_market_data() first.")
        
        if self.current_market_data is None:
            raise ValueError("No market data available for price calculation.")
        
        strike_data = self.current_option_prices[self.current_option_prices['strike'] == strike_price]
        if strike_data.empty:
            raise ValueError(f"Strike price {strike_price} not available")
        
        price = strike_data[side].iloc[0]
        
        # Check for nan values and handle them
        if pd.isna(price) or np.isnan(price):
            print(f"⚠️  Warning: {side} price for strike {strike_price} is NaN, using fallback price")
            # Use a reasonable fallback based on strike and current market price
            current_market_price = self.current_market_data['price'].iloc[-1] / 100  # Convert to decimal
            intrinsic_value = max(current_market_price - strike_price, 0)
            # Add some time value as fallback
            time_value = 0.05 * (1 - strike_price)  # Simple time value estimate
            fallback_price = intrinsic_value + time_value
            return max(0.001, fallback_price)  # Minimum price of 0.001
        
        return float(price)
    
    def calculate_position_limit(self, user_id: str, strike_price: float) -> int:
        """Calculate max position size based on market makers (simplified)"""
        # In a real system, this would check order book depth
        # For now, we'll use a simple calculation based on user's cash and current price
        
        user_cash = self.users[user_id]['current_cash']
        option_ask = self.get_option_price(strike_price, "ask")
        
        # Max 20% of cash in any single strike, minimum 10 contracts available
        max_by_cash = int((user_cash * 0.2) / option_ask) if option_ask > 0 else 0
        base_liquidity = 10  # Minimum liquidity
        
        return max(base_liquidity, max_by_cash)
    
    def execute_trade(self, user_id: str, strike_price: float, quantity: int, 
                     trade_type: TradeType) -> Tuple[bool, str]:
        """Execute a trade for a user"""
        
        # Validation checks
        if user_id not in self.users:
            return False, "User not found"
        
        if self.market_resolved:
            return False, "Market has already resolved - no more trading allowed"
        
        if quantity <= 0:
            return False, "Quantity must be positive"
        
        # Check if market data is available
        if self.current_option_prices is None:
            return False, "No market data available for trading"
        
        # Check position limits
        try:
            position_limit = self.calculate_position_limit(user_id, strike_price)
        except Exception as e:
            return False, f"Error calculating position limit: {str(e)}"
        
        current_position = self.positions[user_id].get(strike_price, Position(user_id, strike_price))
        
        if trade_type == TradeType.BUY and current_position.quantity + quantity > position_limit:
            return False, f"Would exceed position limit of {position_limit} contracts"
        
        # Get prices with error handling
        try:
            if trade_type == TradeType.BUY:
                price_per_contract = self.get_option_price(strike_price, "ask")
                total_cost = quantity * price_per_contract
                
                # Check if user has enough cash
                if self.users[user_id]['current_cash'] < total_cost:
                    return False, f"Insufficient cash. Need ${total_cost:.2f}, have ${self.users[user_id]['current_cash']:.2f}"
                    
            else:  # SELL
                price_per_contract = self.get_option_price(strike_price, "bid")
                total_cost = quantity * price_per_contract  # Positive for sells (they receive money)
                
                # Check if user has enough contracts to sell
                if current_position.quantity < quantity:
                    return False, f"Cannot sell {quantity} contracts, only own {current_position.quantity}"
        
        except Exception as e:
            return False, f"Error getting option price: {str(e)}"
        
        # Validate prices before proceeding
        if pd.isna(price_per_contract) or np.isnan(price_per_contract) or price_per_contract <= 0:
            return False, f"Invalid option price: {price_per_contract}"
        
        if pd.isna(total_cost) or np.isnan(total_cost):
            return False, f"Invalid total cost: {total_cost}"
        
        # Check market data availability for trade execution
        if self.current_market_data is None:
            return False, "No market data available for trade execution"
        
        # Execute the trade
        trade_id = str(uuid.uuid4())
        current_market_price = self.current_market_data['price'].iloc[-1]
        
        trade = Trade(
            trade_id=trade_id,
            user_id=user_id,
            timestamp=datetime.now(),
            trade_type=trade_type,
            strike_price=strike_price,
            quantity=quantity,
            price_per_contract=float(price_per_contract),  # Ensure it's a valid float
            total_cost=float(total_cost) if trade_type == TradeType.BUY else float(-total_cost),
            market_price_at_trade=float(current_market_price)
        )
        
        # Update user's cash
        if trade_type == TradeType.BUY:
            self.users[user_id]['current_cash'] -= total_cost
        else:
            self.users[user_id]['current_cash'] += total_cost
        
        # Update position
        if strike_price not in self.positions[user_id]:
            self.positions[user_id][strike_price] = Position(user_id, strike_price)
        
        self.positions[user_id][strike_price].add_trade(trade)
        
        # Save to database with error handling
        try:
            self._save_trade_to_db(trade)
            self._update_user_cash_in_db(user_id)
        except Exception as e:
            # Rollback the in-memory changes if database save fails
            if trade_type == TradeType.BUY:
                self.users[user_id]['current_cash'] += total_cost
            else:
                self.users[user_id]['current_cash'] -= total_cost
            
            # Remove the trade from position
            if len(self.positions[user_id][strike_price].trades) > 0:
                self.positions[user_id][strike_price].trades.pop()
                # Recalculate position quantities
                self.positions[user_id][strike_price].quantity = sum(
                    t.quantity if t.trade_type == TradeType.BUY else -t.quantity 
                    for t in self.positions[user_id][strike_price].trades
                )
                self.positions[user_id][strike_price].total_cost_basis = sum(
                    t.total_cost for t in self.positions[user_id][strike_price].trades
                )
            
            return False, f"Database error: {str(e)}"
        
        action = "Bought" if trade_type == TradeType.BUY else "Sold"
        print(f"✅ {action} {quantity} contracts at strike {strike_price} for ${abs(total_cost):.2f}")
        
        return True, f"Trade executed successfully"
    
    def _save_trade_to_db(self, trade: Trade):
        """Save trade to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO trades (trade_id, user_id, timestamp, trade_type, strike_price, 
                              quantity, price_per_contract, total_cost, market_price_at_trade)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (trade.trade_id, trade.user_id, trade.timestamp, trade.trade_type.value,
              trade.strike_price, trade.quantity, trade.price_per_contract, 
              trade.total_cost, trade.market_price_at_trade))
        conn.commit()
        conn.close()
    
    def _update_user_cash_in_db(self, user_id: str):
        """Update user's cash balance in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET current_cash = ? WHERE user_id = ?
        ''', (self.users[user_id]['current_cash'], user_id))
        conn.commit()
        conn.close()
    
    def get_user_portfolio(self, user_id: str) -> Dict:
        """Get complete portfolio summary for a user"""
        if user_id not in self.users:
            return {}
        
        user_data = self.users[user_id].copy()
        positions_summary = []
        total_unrealized_pnl = 0.0
        total_position_value = 0.0
        
        for strike, position in self.positions[user_id].items():
            if position.quantity != 0:  # Only show non-zero positions
                current_price = self.get_option_price(strike, "mid")
                unrealized_pnl = position.calculate_unrealized_pnl(current_price)
                position_value = position.quantity * current_price
                
                positions_summary.append({
                    'strike': strike,
                    'quantity': position.quantity,
                    'avg_cost': position.get_average_cost_per_contract(),
                    'current_price': current_price,
                    'position_value': position_value,
                    'unrealized_pnl': unrealized_pnl,
                    'total_cost_basis': position.total_cost_basis
                })
                
                total_unrealized_pnl += unrealized_pnl
                total_position_value += position_value
        
        portfolio = {
            'user_info': user_data,
            'cash': user_data['current_cash'],
            'total_position_value': total_position_value,
            'total_portfolio_value': user_data['current_cash'] + total_position_value,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_realized_pnl': user_data['total_realized_pnl'],
            'total_pnl': total_unrealized_pnl + user_data['total_realized_pnl'],
            'positions': positions_summary
        }
        
        return portfolio
    
    def resolve_market(self, final_market_price: float):
        """Resolve the market and settle all positions"""
        self.market_resolved = True
        self.final_market_price = final_market_price
        
        print(f"🏁 Market resolving at final price: {final_market_price:.2f}")
        
        for user_id in self.users:
            total_settlement = 0.0
            
            for strike, position in self.positions[user_id].items():
                if position.quantity != 0:
                    settlement_value = position.settle_position(final_market_price, strike)
                    total_settlement += settlement_value
                    
                    # Add settlement value to user's cash
                    self.users[user_id]['current_cash'] += settlement_value
                    
                    print(f"👤 {self.users[user_id]['username']}: Strike {strike} position settled for ${settlement_value:.2f}")
            
            # Update realized P&L
            final_portfolio_value = self.users[user_id]['current_cash']
            total_realized_pnl = final_portfolio_value - self.users[user_id]['starting_cash']
            self.users[user_id]['total_realized_pnl'] = total_realized_pnl
            
            self._update_user_cash_in_db(user_id)
        
        print("✅ All positions settled!")
    
    def get_market_summary(self) -> Dict:
        """Get current market and pricing summary"""
        if self.current_market_data is None:
            return {"error": "No market data available"}
        
        current_price = self.current_market_data['price'].iloc[-1]
        
        summary = {
            'current_market_price': current_price,
            'market_resolved': self.market_resolved,
            'available_strikes': self.current_option_prices['strike'].tolist() if self.current_option_prices is not None else [],
            'option_prices': self.current_option_prices.to_dict('records') if self.current_option_prices is not None else []
        }
        
        if self.market_resolved:
            summary['final_price'] = self.final_market_price
        
        return summary

# Example usage and testing functions
def demo_portfolio_system():
    """Demonstrate the portfolio system with sample data"""
    print("🚀 Starting Portfolio System Demo")
    print("=" * 50)
    
    # Initialize portfolio manager
    pm = PortfolioManager()
    
    # Clear previous data for clean demo
    pm.clear_database()
    
    # Create some test users
    alice_id = pm.create_user("Alice", 15000)
    bob_id = pm.create_user("Bob", 15000)
    
    # Create some sample market data (you would use your valid-num-engine.py output)
    sample_market_data = pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=10, freq='5min'),
        'price': [45, 47, 46, 48, 52, 51, 53, 55, 58, 60],  # Market trending up
        'volume': [100, 150, 120, 180, 200, 175, 160, 190, 220, 250]
    })
    
    # Update market data
    pm.update_market_data(sample_market_data)
    
    # Show current market summary
    print("\n📊 Current Market Summary:")
    market_summary = pm.get_market_summary()
    for key, value in market_summary.items():
        if key == 'option_prices':
            print(f"{key}:")
            for option in value:
                print(f"  Strike {option['strike']}: Bid={option['bid']:.4f}, Ask={option['ask']:.4f}")
        else:
            print(f"{key}: {value}")
    
    # Execute some trades
    print("\n💰 Executing Sample Trades:")
    
    # Alice buys some 0.5 strike calls
    success, msg = pm.execute_trade(alice_id, 0.5, 10, TradeType.BUY)
    print(f"Alice trade result: {msg}")
    
    # Bob buys some 0.6 strike calls  
    success, msg = pm.execute_trade(bob_id, 0.6, 5, TradeType.BUY)
    print(f"Bob trade result: {msg}")
    
    # Alice sells some of her position
    success, msg = pm.execute_trade(alice_id, 0.5, 3, TradeType.SELL)
    print(f"Alice sell result: {msg}")
    
    # Show portfolios
    print("\n👥 Portfolio Summaries:")
    for user_id, username in [(alice_id, "Alice"), (bob_id, "Bob")]:
        portfolio = pm.get_user_portfolio(user_id)
        print(f"\n{username}'s Portfolio:")
        print(f"  Cash: ${portfolio['cash']:,.2f}")
        print(f"  Position Value: ${portfolio['total_position_value']:,.2f}")
        print(f"  Total Portfolio: ${portfolio['total_portfolio_value']:,.2f}")
        print(f"  Unrealized P&L: ${portfolio['total_unrealized_pnl']:,.2f}")
        
        for pos in portfolio['positions']:
            print(f"  Strike {pos['strike']}: {pos['quantity']} contracts @ ${pos['avg_cost']:.4f} avg")
    
    # Simulate market resolution
    print("\n🏁 Resolving Market at 65...")
    pm.resolve_market(65.0)
    
    # Show final portfolios
    print("\n📈 Final Portfolio Results:")
    for user_id, username in [(alice_id, "Alice"), (bob_id, "Bob")]:
        portfolio = pm.get_user_portfolio(user_id)
        print(f"\n{username} Final Results:")
        print(f"  Final Cash: ${portfolio['cash']:,.2f}")
        print(f"  Total Realized P&L: ${portfolio['total_realized_pnl']:,.2f}")
        profit_pct = (portfolio['total_realized_pnl'] / 15000) * 100
        print(f"  Return: {profit_pct:.2f}%")

def demo_with_existing_users():
    """Alternative demo that works with existing users (doesn't clear database)"""
    import random
    
    print("🚀 Starting Portfolio System Demo (Preserving Existing Data)")
    print("=" * 60)
    
    # Initialize portfolio manager (loads existing users)
    pm = PortfolioManager()
    
    # Create users with unique names to avoid conflicts
    timestamp = datetime.now().strftime("%H%M%S")
    alice_id = pm.create_user(f"Alice_{timestamp}", 15000)
    bob_id = pm.create_user(f"Bob_{timestamp}", 15000)
    
    # Create some sample market data (you would use your valid-num-engine.py output)
    sample_market_data = pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=10, freq='5min'),
        'price': [45, 47, 46, 48, 52, 51, 53, 55, 58, 60],  # Market trending up
        'volume': [100, 150, 120, 180, 200, 175, 160, 190, 220, 250]
    })
    
    # Update market data
    pm.update_market_data(sample_market_data)
    
    # Show current market summary
    print("\n📊 Current Market Summary:")
    market_summary = pm.get_market_summary()
    for key, value in market_summary.items():
        if key == 'option_prices':
            print(f"{key}:")
            for option in value:
                print(f"  Strike {option['strike']}: Bid={option['bid']:.4f}, Ask={option['ask']:.4f}")
        else:
            print(f"{key}: {value}")
    
    # Execute some trades
    print("\n💰 Executing Sample Trades:")
    
    # Alice buys some 0.5 strike calls
    success, msg = pm.execute_trade(alice_id, 0.5, 10, TradeType.BUY)
    print(f"Alice trade result: {msg}")
    
    # Bob buys some 0.6 strike calls  
    success, msg = pm.execute_trade(bob_id, 0.6, 5, TradeType.BUY)
    print(f"Bob trade result: {msg}")
    
    # Alice sells some of her position
    success, msg = pm.execute_trade(alice_id, 0.5, 3, TradeType.SELL)
    print(f"Alice sell result: {msg}")
    
    # Show portfolios
    print("\n👥 Portfolio Summaries:")
    for user_id, username in [(alice_id, "Alice"), (bob_id, "Bob")]:
        portfolio = pm.get_user_portfolio(user_id)
        print(f"\n{username}'s Portfolio:")
        print(f"  Cash: ${portfolio['cash']:,.2f}")
        print(f"  Position Value: ${portfolio['total_position_value']:,.2f}")
        print(f"  Total Portfolio: ${portfolio['total_portfolio_value']:,.2f}")
        print(f"  Unrealized P&L: ${portfolio['total_unrealized_pnl']:,.2f}")
        
        for pos in portfolio['positions']:
            print(f"  Strike {pos['strike']}: {pos['quantity']} contracts @ ${pos['avg_cost']:.4f} avg")
    
    # Simulate market resolution
    print("\n🏁 Resolving Market at 65...")
    pm.resolve_market(65.0)
    
    # Show final portfolios
    print("\n📈 Final Portfolio Results:")
    for user_id, username in [(alice_id, "Alice"), (bob_id, "Bob")]:
        portfolio = pm.get_user_portfolio(user_id)
        print(f"\n{username} Final Results:")
        print(f"  Final Cash: ${portfolio['cash']:,.2f}")
        print(f"  Total Realized P&L: ${portfolio['total_realized_pnl']:,.2f}")
        profit_pct = (portfolio['total_realized_pnl'] / 15000) * 100
        print(f"  Return: {profit_pct:.2f}%")

if __name__ == "__main__":
    demo_portfolio_system()