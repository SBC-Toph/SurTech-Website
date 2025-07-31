from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import sys
from pathlib import Path
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional

# Add src to path for imports
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir / "src"))

# Import our modules
from data_generation.live_simulator import LiveMarketSimulator, PortfolioIntegrator  # type: ignore
from portfolio.portfolio_manager import PortfolioManager, TradeType  # type: ignore

# Global instances
simulator: Optional[LiveMarketSimulator] = None
portfolio_manager: Optional[PortfolioManager] = None
integrator: Optional[PortfolioIntegrator] = None
websocket_connections: List[WebSocket] = []

app = FastAPI(
    title="Trading Platform API",
    description="Real-time prediction market trading platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    global portfolio_manager
    print("Starting Trading Platform API...")
    portfolio_manager = PortfolioManager(db_path="data/databases/trading_platform.db")
    print("Portfolio manager initialized")

@app.on_event("shutdown")
async def shutdown_event():
    global simulator
    if simulator:
        simulator.stop()

@app.get("/")
async def root():
    return {"message": "Trading Platform API", "docs": "/docs"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "simulator_active": simulator is not None,
        "portfolio_manager_active": portfolio_manager is not None
    }

def get_simulator() -> LiveMarketSimulator:
    global simulator
    if simulator is None:
        raise HTTPException(status_code=404, detail="No active simulation")
    return simulator

def get_portfolio_manager() -> PortfolioManager:
    global portfolio_manager
    if portfolio_manager is None:
        raise HTTPException(status_code=500, detail="Portfolio manager not initialized")
    return portfolio_manager

# Market endpoints
@app.post("/api/market/start")
async def start_simulation(
    total_points: int = 100,
    initial_price: float = 50.0,
    volatility: float = 1.8,
    time_interval: float = 1.0
):
    global simulator, integrator
    
    if simulator and simulator.simulation_state.value in ["RUNNING", "PAUSED"]:
        raise HTTPException(status_code=400, detail="Simulation already running")
    
    try:
        simulator = LiveMarketSimulator(
            total_points=total_points,
            initial_price=initial_price,
            volatility=volatility,
            save_to_csv=True
        )
        
        simulator.start_live_simulation(time_interval=time_interval, mode="auto")
        
        portfolio_mgr = get_portfolio_manager()
        integrator = PortfolioIntegrator(simulator, portfolio_mgr)
        
        return {
            "status": "started",
            "message": f"Simulation started with {total_points} points",
            "current_price": simulator.get_current_price(),
            "target_resolution": "YES" if simulator.final_resolution else "NO"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market/status")
async def get_market_status():
    sim = get_simulator()
    stats = sim.get_simulation_stats()
    return {
        "status": stats['state'].lower(),
        "current_price": stats['current_price'],
        "progress_percent": stats['progress_percent'],
        "target_resolution": stats['target_resolution']
    }

@app.get("/api/market/current")
async def get_current_market_data():
    sim = get_simulator()
    current_data = sim.get_current_data_point()
    if not current_data:
        raise HTTPException(status_code=404, detail="No current data")
    return current_data

# Portfolio endpoints
@app.post("/api/portfolio/create-user")
async def create_user(username: str, starting_cash: float = 15000.0):
    pm = get_portfolio_manager()
    try:
        user_id = pm.create_user(username, starting_cash)
        user_data = pm.users[user_id]
        return {
            "user_id": user_id,
            "username": user_data['username'],
            "starting_cash": user_data['starting_cash'],
            "current_cash": user_data['current_cash']
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/portfolio/{user_id}")
async def get_portfolio(user_id: str):
    pm = get_portfolio_manager()
    if user_id not in pm.users:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        portfolio = pm.get_user_portfolio(user_id)
        return portfolio
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Trading endpoints
@app.post("/api/trading/execute")
async def execute_trade(
    user_id: str,
    strike_price: float,
    quantity: int,
    trade_type: str
):
    pm = get_portfolio_manager()
    
    if user_id not in pm.users:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        trade_enum = TradeType.BUY if trade_type == "BUY" else TradeType.SELL
        success, message = pm.execute_trade(user_id, strike_price, quantity, trade_enum)
        
        return {
            "success": success,
            "message": message,
            "new_cash_balance": pm.users[user_id]['current_cash'] if success else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trading/option-prices")
async def get_option_prices():
    pm = get_portfolio_manager()
    sim = get_simulator()
    
    try:
        current_price = sim.get_current_price()
        strikes = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        
        option_prices = []
        for strike in strikes:
            try:
                bid = pm.get_option_price(strike, "bid")
                ask = pm.get_option_price(strike, "ask")
                option_prices.append({
                    "strike": strike,
                    "bid": bid,
                    "ask": ask,
                    "mid": (bid + ask) / 2
                })
            except:
                continue
        
        return {
            "current_market_price": current_price,
            "option_prices": option_prices,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)