#!/usr/bin/env python3
"""
Start the Trading Platform API
"""

import uvicorn
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    print("Starting Trading Platform API...")
    print("API Documentation will be available at: http://localhost:8000/docs")
    print("API will be running at: http://localhost:8000")
    print("WebSocket endpoint: ws://localhost:8000/ws/market")
    print()
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
