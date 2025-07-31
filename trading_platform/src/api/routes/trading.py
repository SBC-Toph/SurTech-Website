"""
Trading API routes
Save this as: trading_platform/src/api/routes/trading.py
"""

from fastapi import APIRouter, HTTPException, Request
from datetime import datetime

from api.schemas.market import (
    ExecuteTradeRequest, 
    TradeResponse,
    OptionPricesResponse,
    OptionPriceResponse
)
from portfolio.portfolio_manager import TradeType  # type: ignore

router = APIRouter()

@router.post("/execute", response_model=TradeResponse)
async def execute_trade(request: ExecuteTradeRequest, app_request: Request):
    """Execute a trade (buy or sell option contracts)"""
    
    portfolio_manager = app_request.app.state.get_portfolio_manager()
    
    # Check if user exists
    if request.user_id not in portfolio_manager.users:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Convert trade type string to enum
    try:
        trade_type = TradeType.BUY if request.trade_type == "BUY" else TradeType.SELL
    except:
        raise HTTPException(status_code=400, detail="Invalid trade type. Must be 'BUY' or 'SELL'")
    
    try:
        # Execute the trade
        success, message = portfolio_manager.execute_trade(
            user_id=request.user_id,
            strike_price=request.strike_price,
            quantity=request.quantity,
            trade_type=trade_type
        )
        
        if success:
            # Get updated user info
            user_data = portfolio_manager.users[request.user_id]
            
            # Get trade details for response
            option_price = portfolio_manager.get_option_price(
                request.strike_price, 
                "ask" if trade_type == TradeType.BUY else "bid"
            )
            total_cost = option_price * request.quantity
            
            return TradeResponse(
                success=True,
                message=message,
                trade_id=f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                price_per_contract=option_price,
                total_cost=total_cost,
                new_cash_balance=user_data['current_cash']
            )
        else:
            return TradeResponse(
                success=False,
                message=message
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trade execution failed: {str(e)}")

@router.get("/option-prices", response_model=OptionPricesResponse)
async def get_option_prices(app_request: Request):
    """Get current option prices for all available strikes"""
    
    portfolio_manager = app_request.app.state.get_portfolio_manager()
    simulator = app_request.app.state.get_simulator()
    
    try:
        # Get current market price
        current_market_price = simulator.get_current_price()
        
        # Get option prices from portfolio manager
        if hasattr(portfolio_manager, 'current_option_prices') and portfolio_manager.current_option_prices is not None:
            option_data = portfolio_manager.current_option_prices.to_dict('records')
        else:
            # If no current prices, create basic ones
            strikes = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
            option_data = []
            for strike in strikes:
                try:
                    bid = portfolio_manager.get_option_price(strike, "bid")
                    ask = portfolio_manager.get_option_price(strike, "ask")
                    mid = (bid + ask) / 2
                    option_data.append({
                        'strike': strike,
                        'bid': bid,
                        'ask': ask,
                        'mid': mid
                    })
                except:
                    # If pricing fails, skip this strike
                    continue
        
        # Convert to response format
        option_prices = []
        for option in option_data:
            option_prices.append(OptionPriceResponse(
                strike=option['strike'],
                bid=option['bid'],
                ask=option['ask'],
                mid=option['mid']
            ))
        
        return OptionPricesResponse(
            current_market_price=current_market_price,
            option_prices=option_prices,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get option prices: {str(e)}")

@router.get("/option-prices/{strike_price}")
async def get_option_price_for_strike(strike_price: float, app_request: Request):
    """Get option price for a specific strike"""
    
    portfolio_manager = app_request.app.state.get_portfolio_manager()
    
    if strike_price < 0 or strike_price > 1:
        raise HTTPException(status_code=400, detail="Strike price must be between 0 and 1")
    
    try:
        bid = portfolio_manager.get_option_price(strike_price, "bid")
        ask = portfolio_manager.get_option_price(strike_price, "ask")
        mid = (bid + ask) / 2
        
        return OptionPriceResponse(
            strike=strike_price,
            bid=bid,
            ask=ask,
            mid=mid
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get option price: {str(e)}")

@router.get("/market-summary")
async def get_market_summary(app_request: Request):
    """Get trading market summary"""
    
    portfolio_manager = app_request.app.state.get_portfolio_manager()
    simulator = app_request.app.state.get_simulator()
    
    try:
        market_summary = portfolio_manager.get_market_summary()
        sim_stats = simulator.get_simulation_stats()
        
        return {
            "market_summary": market_summary,
            "simulation_stats": sim_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market summary: {str(e)}")

@router.post("/resolve-market")
async def resolve_market(final_price: float, app_request: Request):
    """Resolve the market at a final price (settle all positions)"""
    
    portfolio_manager = app_request.app.state.get_portfolio_manager()
    
    if final_price < 0 or final_price > 100:
        raise HTTPException(status_code=400, detail="Final price must be between 0 and 100")
    
    try:
        # Resolve the market
        portfolio_manager.resolve_market(final_price)
        
        # Stop the simulator if running
        simulator = app_request.app.state.get_simulator()
        simulator.stop()
        
        return {
            "success": True,
            "message": f"Market resolved at ${final_price:.2f}",
            "final_price": final_price,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve market: {str(e)}")

@router.get("/trade-history/{user_id}")
async def get_trade_history(user_id: str, app_request: Request):
    """Get trade history for a user"""
    
    portfolio_manager = app_request.app.state.get_portfolio_manager()
    
    if user_id not in portfolio_manager.users:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        trades = []
        
        # Get trades from user's positions
        if user_id in portfolio_manager.positions:
            for strike, position in portfolio_manager.positions[user_id].items():
                for trade in position.trades:
                    trades.append({
                        "trade_id": trade.trade_id,
                        "timestamp": trade.timestamp.isoformat(),
                        "trade_type": trade.trade_type.value,
                        "strike_price": trade.strike_price,
                        "quantity": trade.quantity,
                        "price_per_contract": trade.price_per_contract,
                        "total_cost": trade.total_cost,
                        "market_price_at_trade": trade.market_price_at_trade
                    })
        
        # Sort by timestamp (most recent first)
        trades.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            "user_id": user_id,
            "trades": trades,
            "total_trades": len(trades)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trade history: {str(e)}")

@router.get("/position-limits/{user_id}")
async def get_position_limits(user_id: str, app_request: Request):
    """Get position limits for a user"""
    
    portfolio_manager = app_request.app.state.get_portfolio_manager()
    
    if user_id not in portfolio_manager.users:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Get limits for different strikes
        strikes = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        limits = {}
        
        for strike in strikes:
            try:
                limit = portfolio_manager.calculate_position_limit(user_id, strike)
                limits[str(strike)] = limit
            except:
                limits[str(strike)] = 0
        
        return {
            "user_id": user_id,
            "position_limits": limits,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get position limits: {str(e)}")