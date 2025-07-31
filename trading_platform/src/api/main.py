#!/usr/bin/env python3
"""
FastAPI main application
Save this as: trading_platform/src/api/main.py
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

# Import API routes and models
from api.routes.market import router as market_router
from api.routes.portfolio import router as portfolio_router
from api.routes.trading import router as trading_router
from api.schemas.responses import MarketStatusResponse

# Global instances (in production, use dependency injection)
simulator: Optional[LiveMarketSimulator] = None
portfolio_manager: Optional[PortfolioManager] = None
integrator: Optional[PortfolioIntegrator] = None
websocket_connections: List[WebSocket] = []

# FastAPI app
app = FastAPI(
    title="Trading Platform API",
    description="Real-time prediction market trading platform with live simulation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(market_router, prefix="/api/market", tags=["Market"])
app.include_router(portfolio_router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(trading_router, prefix="/api/trading", tags=["Trading"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global portfolio_manager
    
    print("🚀 Starting Trading Platform API...")
    
    # Initialize portfolio manager
    portfolio_manager = PortfolioManager(db_path="data/databases/trading_platform.db")
    print("✅ Portfolio manager initialized")
    
    print("🎯 API ready! Visit http://localhost:8000/docs for interactive docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global simulator
    
    print("🛑 Shutting down Trading Platform API...")
    
    if simulator:
        simulator.stop()
        print("✅ Simulator stopped")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with basic info"""
    return """
    <html>
        <head>
            <title>Trading Platform API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; }
                .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .method { display: inline-block; padding: 4px 8px; border-radius: 3px; color: white; font-weight: bold; }
                .get { background-color: #61affe; }
                .post { background-color: #49cc90; }
                .delete { background-color: #f93e3e; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 Trading Platform API</h1>
                <p>Real-time prediction market trading platform</p>
                
                <h2>📊 Quick Links</h2>
                <ul>
                    <li><a href="/docs">📖 Interactive API Documentation</a></li>
                    <li><a href="/redoc">📚 ReDoc Documentation</a></li>
                </ul>
                
                <h2>🔗 Key Endpoints</h2>
                
                <div class="endpoint">
                    <span class="method post">POST</span>
                    <strong>/api/market/start</strong> - Start market simulation
                </div>
                
                <div class="endpoint">
                    <span class="method get">GET</span>
                    <strong>/api/market/status</strong> - Get current market status
                </div>
                
                <div class="endpoint">
                    <span class="method get">GET</span>
                    <strong>/api/market/current</strong> - Get current market price
                </div>
                
                <div class="endpoint">
                    <span class="method post">POST</span>
                    <strong>/api/portfolio/create-user</strong> - Create trading account
                </div>
                
                <div class="endpoint">
                    <span class="method post">POST</span>
                    <strong>/api/trading/execute</strong> - Execute trades
                </div>
                
                <div class="endpoint">
                    <span class="method get">GET</span>
                    <strong>/ws/market</strong> - WebSocket for real-time updates
                </div>
                
                <h2>🚀 Getting Started</h2>
                <ol>
                    <li>Start a market simulation: <code>POST /api/market/start</code></li>
                    <li>Create a user account: <code>POST /api/portfolio/create-user</code></li>
                    <li>Execute trades: <code>POST /api/trading/execute</code></li>
                    <li>Monitor in real-time: <code>ws://localhost:8000/ws/market</code></li>
                </ol>
            </div>
        </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "simulator_active": simulator is not None and simulator.simulation_state.value != "STOPPED",
        "portfolio_manager_active": portfolio_manager is not None
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws/market")
async def websocket_market_updates(websocket: WebSocket):
    """WebSocket endpoint for real-time market updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive and send periodic updates
            if simulator and simulator.current_data_point:
                data = {
                    "type": "market_update",
                    "timestamp": datetime.now().isoformat(),
                    "price": simulator.get_current_price(),
                    "data_point": simulator.current_data_point
                }
                await websocket.send_text(json.dumps(data))
            
            await asyncio.sleep(1)  # Send updates every second
            
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
        print(f"WebSocket client disconnected. Active connections: {len(websocket_connections)}")

async def broadcast_to_websockets(data: dict):
    """Broadcast data to all connected WebSocket clients"""
    if not websocket_connections:
        return
    
    message = json.dumps(data)
    disconnected = []
    
    for websocket in websocket_connections:
        try:
            await websocket.send_text(message)
        except:
            disconnected.append(websocket)
    
    # Remove disconnected clients
    for ws in disconnected:
        websocket_connections.remove(ws)

def get_simulator() -> LiveMarketSimulator:
    """Get the global simulator instance"""
    global simulator
    if simulator is None:
        raise HTTPException(status_code=404, detail="No active simulation. Start one first.")
    return simulator

def get_portfolio_manager() -> PortfolioManager:
    """Get the global portfolio manager instance"""
    global portfolio_manager
    if portfolio_manager is None:
        raise HTTPException(status_code=500, detail="Portfolio manager not initialized")
    return portfolio_manager

def get_integrator() -> PortfolioIntegrator:
    """Get the global integrator instance"""
    global integrator
    if integrator is None:
        raise HTTPException(status_code=404, detail="No active integration. Start simulation first.")
    return integrator

# Export globals for use in routes
app.state.simulator = None
app.state.portfolio_manager = None
app.state.integrator = None
app.state.websocket_connections = websocket_connections

# Make functions available to routes
app.state.get_simulator = get_simulator
app.state.get_portfolio_manager = get_portfolio_manager
app.state.get_integrator = get_integrator
app.state.broadcast_to_websockets = broadcast_to_websockets

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )