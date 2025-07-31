"""
Portfolio API routes
Save this as: trading_platform/src/api/routes/portfolio.py
"""

from fastapi import APIRouter, HTTPException, Request
from typing import List

from api.schemas.market import (
    CreateUserRequest, 
    UserResponse, 
    PortfolioResponse,
    PositionResponse
)

router = APIRouter()

@router.post("/create-user", response_model=UserResponse)
async def create_user(request: CreateUserRequest, app_request: Request):
    """Create a new trading user account"""
    
    portfolio_manager = app_request.app.state.get_portfolio_manager()
    
    try:
        # Create user
        user_id = portfolio_manager.create_user(
            username=request.username,
            starting_cash=request.starting_cash
        )
        
        # Get user info to return
        user_data = portfolio_manager.users[user_id]
        
        return UserResponse(
            user_id=user_id,
            username=user_data['username'],
            starting_cash=user_data['starting_cash'],
            current_cash=user_data['current_cash'],
            total_realized_pnl=user_data['total_realized_pnl']
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create user: {str(e)}")

@router.get("/users", response_model=List[UserResponse])
async def list_users(app_request: Request):
    """List all trading users"""
    
    portfolio_manager = app_request.app.state.get_portfolio_manager()
    
    users = []
    for user_id, user_data in portfolio_manager.users.items():
        users.append(UserResponse(
            user_id=user_id,
            username=user_data['username'],
            starting_cash=user_data['starting_cash'],
            current_cash=user_data['current_cash'],
            total_realized_pnl=user_data['total_realized_pnl']
        ))
    
    return users

@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, app_request: Request):
    """Get specific user information"""
    
    portfolio_manager = app_request.app.state.get_portfolio_manager()
    
    if user_id not in portfolio_manager.users:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = portfolio_manager.users[user_id]
    
    return UserResponse(
        user_id=user_id,
        username=user_data['username'],
        starting_cash=user_data['starting_cash'],
        current_cash=user_data['current_cash'],
        total_realized_pnl=user_data['total_realized_pnl']
    )

@router.get("/{user_id}", response_model=PortfolioResponse)
async def get_portfolio(user_id: str, app_request: Request):
    """Get complete portfolio for a user"""
    
    portfolio_manager = app_request.app.state.get_portfolio_manager()
    
    if user_id not in portfolio_manager.users:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        portfolio = portfolio_manager.get_user_portfolio(user_id)
        
        # Convert positions to response format
        positions = []
        for pos in portfolio['positions']:
            positions.append(PositionResponse(
                strike=pos['strike'],
                quantity=pos['quantity'],
                avg_cost=pos['avg_cost'],
                current_price=pos['current_price'],
                position_value=pos['position_value'],
                unrealized_pnl=pos['unrealized_pnl'],
                total_cost_basis=pos['total_cost_basis']
            ))
        
        # Convert user info
        user_info = UserResponse(
            user_id=user_id,
            username=portfolio['user_info']['username'],
            starting_cash=portfolio['user_info']['starting_cash'],
            current_cash=portfolio['user_info']['current_cash'],
            total_realized_pnl=portfolio['user_info']['total_realized_pnl']
        )
        
        return PortfolioResponse(
            user_info=user_info,
            cash=portfolio['cash'],
            total_position_value=portfolio['total_position_value'],
            total_portfolio_value=portfolio['total_portfolio_value'],
            total_unrealized_pnl=portfolio['total_unrealized_pnl'],
            total_realized_pnl=portfolio['total_realized_pnl'],
            total_pnl=portfolio['total_pnl'],
            positions=positions
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio: {str(e)}")

@router.get("/{user_id}/positions", response_model=List[PositionResponse])
async def get_user_positions(user_id: str, app_request: Request):
    """Get only the positions for a user"""
    
    portfolio_manager = app_request.app.state.get_portfolio_manager()
    
    if user_id not in portfolio_manager.users:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        portfolio = portfolio_manager.get_user_portfolio(user_id)
        
        positions = []
        for pos in portfolio['positions']:
            positions.append(PositionResponse(
                strike=pos['strike'],
                quantity=pos['quantity'],
                avg_cost=pos['avg_cost'],
                current_price=pos['current_price'],
                position_value=pos['position_value'],
                unrealized_pnl=pos['unrealized_pnl'],
                total_cost_basis=pos['total_cost_basis']
            ))
        
        return positions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get positions: {str(e)}")

@router.delete("/{user_id}")
async def delete_user(user_id: str, app_request: Request):
    """Delete a user account (for testing purposes)"""
    
    portfolio_manager = app_request.app.state.get_portfolio_manager()
    
    if user_id not in portfolio_manager.users:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Remove from memory
        del portfolio_manager.users[user_id]
        if user_id in portfolio_manager.positions:
            del portfolio_manager.positions[user_id]
        
        # Note: In a real system, you'd also clean up the database
        # For now, we'll just remove from memory
        
        return {"success": True, "message": f"User {user_id} deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

@router.post("/clear-database")
async def clear_database(app_request: Request):
    """Clear all portfolio data (for testing purposes)"""
    
    portfolio_manager = app_request.app.state.get_portfolio_manager()
    
    try:
        portfolio_manager.clear_database()
        return {"success": True, "message": "Database cleared successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear database: {str(e)}")