"""
Market API routes
Save this as: trading_platform/src/api/routes/market.py
"""

from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
import pandas as pd
from datetime import datetime

from api.schemas.market import (
    StartSimulationRequest, 
    MarketStatusResponse, 
    MarketDataResponse,
    HistoricalDataResponse
)
from data_generation.live_simulator import LiveMarketSimulator, PortfolioIntegrator  # type: ignore
from portfolio.portfolio_manager import PortfolioManager  # type: ignore

router = APIRouter()

@router.post("/start", response_model=MarketStatusResponse)
async def start_simulation(request: StartSimulationRequest, app_request: Request):
    """Start a new market simulation"""
    
    # Check if simulation already running
    if hasattr(app_request.app.state, 'simulator') and app_request.app.state.simulator:
        current_sim = app_request.app.state.simulator
        if current_sim.simulation_state.value in ["RUNNING", "PAUSED"]:
            raise HTTPException(
                status_code=400, 
                detail="Simulation already running. Stop it first."
            )
    
    try:
        # Create new simulator
        simulator = LiveMarketSimulator(
            total_points=request.total_points,
            initial_price=request.initial_price,
            volatility=request.volatility,
            threshold_percentage=request.threshold_percentage,
            trend_strength=request.trend_strength,
            max_movement=request.max_movement,
            save_to_csv=request.save_to_csv
        )
        
        # Start simulation
        simulator.start_live_simulation(
            time_interval=request.time_interval,
            mode=request.mode
        )
        
        # Set up integration with portfolio manager if available
        portfolio_manager = app_request.app.state.get_portfolio_manager()
        integrator = PortfolioIntegrator(simulator, portfolio_manager)
        
        # Store in app state
        app_request.app.state.simulator = simulator
        app_request.app.state.integrator = integrator
        
        # Set up real-time callback for WebSocket broadcasting
        def websocket_callback(data_point):
            """Callback to broadcast updates via WebSocket"""
            # This would need to be handled differently in a real async context
            pass
        
        simulator.add_price_update_callback(websocket_callback)
        
        return MarketStatusResponse(
            status="started",
            message=f"Simulation started with {request.total_points} points",
            simulator_id=id(simulator),
            current_price=simulator.get_current_price(),
            progress_percent=0.0,
            is_trending=False,
            target_resolution="YES" if simulator.final_resolution else "NO"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start simulation: {str(e)}")

@router.post("/stop")
async def stop_simulation(app_request: Request):
    """Stop the current simulation"""
    
    simulator = app_request.app.state.get_simulator()
    simulator.stop()
    
    # Clear from app state
    app_request.app.state.simulator = None
    app_request.app.state.integrator = None
    
    return {"status": "stopped", "message": "Simulation stopped successfully"}

@router.post("/pause")
async def pause_simulation(app_request: Request):
    """Pause the current simulation"""
    
    simulator = app_request.app.state.get_simulator()
    simulator.pause()
    
    return {"status": "paused", "message": "Simulation paused"}

@router.post("/resume")
async def resume_simulation(app_request: Request):
    """Resume the paused simulation"""
    
    simulator = app_request.app.state.get_simulator()
    simulator.resume()
    
    return {"status": "resumed", "message": "Simulation resumed"}

@router.get("/status", response_model=MarketStatusResponse)
async def get_market_status(app_request: Request):
    """Get current market simulation status"""
    
    simulator = app_request.app.state.get_simulator()
    stats = simulator.get_simulation_stats()
    
    return MarketStatusResponse(
        status=stats['state'].lower(),
        message=f"Simulation {stats['state'].lower()}",
        simulator_id=id(simulator),
        current_price=stats['current_price'],
        progress_percent=stats['progress_percent'],
        is_trending=stats['is_trending'],
        target_resolution=stats['target_resolution'],
        current_point=stats['current_point'],
        total_points=stats['total_points'],
        time_interval=stats['time_interval']
    )

@router.get("/current", response_model=MarketDataResponse)
async def get_current_market_data(app_request: Request):
    """Get current market data point"""
    
    simulator = app_request.app.state.get_simulator()
    current_data = simulator.get_current_data_point()
    
    if not current_data:
        raise HTTPException(status_code=404, detail="No current data available")
    
    return MarketDataResponse(
        timestamp=current_data['timestamp'],
        price=current_data['price'],
        movement=current_data['movement'],
        volume=current_data['volume'],
        bid_ask_spread=current_data['bid_ask_spread']
    )

@router.get("/history", response_model=HistoricalDataResponse)
async def get_market_history(
    app_request: Request,
    limit: Optional[int] = 100,
    start_point: Optional[int] = None,
    end_point: Optional[int] = None
):
    """Get historical market data"""
    
    simulator = app_request.app.state.get_simulator()
    
    if start_point is not None or end_point is not None:
        # Get specific range
        if not hasattr(simulator, 'get_history_by_point_range'):
            # If method doesn't exist, fall back to recent history
            data = simulator.get_recent_history(limit or 100)
        else:
            df = simulator.get_history_by_point_range(start_point, end_point)
            data = df.to_dict('records') if not df.empty else []
    else:
        # Get recent history
        data = simulator.get_recent_history(limit or 100)
    
    # Convert to response format
    data_points = []
    for point in data:
        data_points.append(MarketDataResponse(
            timestamp=point['timestamp'],
            price=point['price'],
            movement=point['movement'],
            volume=point['volume'],
            bid_ask_spread=point['bid_ask_spread']
        ))
    
    return HistoricalDataResponse(
        data_points=data_points,
        total_points=len(data_points),
        start_time=data_points[0].timestamp if data_points else None,
        end_time=data_points[-1].timestamp if data_points else None
    )

@router.get("/chart-data")
async def get_chart_data(
    app_request: Request,
    limit: Optional[int] = 50
):
    """Get data formatted for charting"""
    
    simulator = app_request.app.state.get_simulator()
    recent_data = simulator.get_recent_history(limit or 50)
    
    if not recent_data:
        return {
            "labels": [],
            "prices": [],
            "volumes": [],
            "movements": []
        }
    
    return {
        "labels": [d['timestamp'].strftime('%H:%M:%S') for d in recent_data],
        "prices": [d['price'] for d in recent_data],
        "volumes": [d['volume'] for d in recent_data],
        "movements": [d['movement'] for d in recent_data],
        "timestamps": [d['timestamp'].isoformat() for d in recent_data]
    }

@router.post("/step")
async def manual_step(app_request: Request):
    """Generate next data point manually (for manual mode)"""
    
    simulator = app_request.app.state.get_simulator()
    
    if simulator.simulation_state.value not in ["PAUSED", "STOPPED"]:
        raise HTTPException(
            status_code=400, 
            detail="Can only step manually when simulation is paused or stopped"
        )
    
    data_point = simulator.step()
    
    if data_point is None:
        return {"status": "completed", "message": "Simulation completed"}
    
    return {
        "status": "stepped",
        "message": "Generated next data point",
        "data_point": {
            "timestamp": data_point['timestamp'].isoformat(),
            "price": data_point['price'],
            "movement": data_point['movement'],
            "volume": data_point['volume']
        }
    }