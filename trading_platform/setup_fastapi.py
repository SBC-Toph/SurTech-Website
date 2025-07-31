#!/usr/bin/env python3
"""
FastAPI Setup Script - Windows Compatible (No Unicode Issues)
Save this as: trading_platform/setup_fastapi_fixed.py
"""

import os
import sys
from pathlib import Path
import subprocess

def install_dependencies():
    """Install required FastAPI dependencies"""
    
    print("Installing FastAPI dependencies...")
    
    dependencies = [
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.22.0",
        "websockets>=11.0",
        "python-multipart>=0.0.6",
        "pydantic>=2.0.0"
    ]
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to install {dep}")
            print(result.stderr)
        else:
            print(f"Installed {dep}")

def create_api_structure():
    """Create the API directory structure"""
    
    print("Creating API directory structure...")
    
    base_dir = Path("src/api")
    
    directories = [
        "routes",
        "schemas", 
        "middleware",
        "utils"
    ]
    
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py files
        init_file = dir_path / "__init__.py"
        init_file.touch()
        
        print(f"Created {dir_path}")

def create_startup_script():
    """Create a startup script for the API"""
    
    startup_script = '''#!/usr/bin/env python3
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
'''
    
    with open("start_api.py", "w", encoding='utf-8') as f:
        f.write(startup_script)
    
    print("Created start_api.py")

def create_requirements_update():
    """Update requirements.txt with FastAPI dependencies"""
    
    additional_requirements = """
# FastAPI and web server
fastapi>=0.100.0
uvicorn[standard]>=0.22.0
websockets>=11.0
python-multipart>=0.0.6
pydantic>=2.0.0

# Development tools
python-dotenv>=1.0.0
"""
    
    # Read existing requirements
    try:
        with open("requirements.txt", "r", encoding='utf-8') as f:
            existing = f.read()
    except FileNotFoundError:
        existing = ""
    
    # Add new requirements if not already present
    with open("requirements.txt", "w", encoding='utf-8') as f:
        f.write(existing)
        if "fastapi" not in existing.lower():
            f.write(additional_requirements)
    
    print("Updated requirements.txt")

def create_example_client():
    """Create an example client script to test the API"""
    
    client_script = '''#!/usr/bin/env python3
"""
Example API client for testing
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api():
    """Test the trading platform API"""
    
    print("Testing Trading Platform API")
    print("=" * 40)
    
    # Test health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    # Start simulation
    print("\\n2. Starting simulation...")
    sim_config = {
        "total_points": 50,
        "initial_price": 50.0,
        "volatility": 2.0,
        "time_interval": 0.5,
        "mode": "auto"
    }
    try:
        response = requests.post(f"{BASE_URL}/api/market/start", json=sim_config)
        print(f"Simulation started: {response.json()}")
    except Exception as e:
        print(f"Failed to start simulation: {e}")
        return
    
    # Create user
    print("\\n3. Creating user...")
    user_data = {
        "username": "test_user",
        "starting_cash": 10000.0
    }
    try:
        response = requests.post(f"{BASE_URL}/api/portfolio/create-user", json=user_data)
        user_result = response.json()
        user_id = user_result["user_id"]
        print(f"User created: {user_result}")
    except Exception as e:
        print(f"Failed to create user: {e}")
        return
    
    # Wait for some market data
    print("\\n4. Waiting for market data...")
    time.sleep(3)
    
    # Get market status
    try:
        response = requests.get(f"{BASE_URL}/api/market/status")
        print(f"Market status: {response.json()}")
    except Exception as e:
        print(f"Failed to get market status: {e}")
    
    # Execute a trade
    print("\\n5. Executing trade...")
    trade_data = {
        "user_id": user_id,
        "strike_price": 0.5,
        "quantity": 5,
        "trade_type": "BUY"
    }
    try:
        response = requests.post(f"{BASE_URL}/api/trading/execute", json=trade_data)
        print(f"Trade result: {response.json()}")
    except Exception as e:
        print(f"Failed to execute trade: {e}")
    
    # Get portfolio
    print("\\n6. Getting portfolio...")
    try:
        response = requests.get(f"{BASE_URL}/api/portfolio/{user_id}")
        print(f"Portfolio: {response.json()}")
    except Exception as e:
        print(f"Failed to get portfolio: {e}")
    
    print("\\nAPI test completed!")

if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("Cannot connect to API. Make sure it's running at http://localhost:8000")
    except Exception as e:
        print(f"Test failed: {e}")
'''
    
    with open("test_api_client.py", "w", encoding='utf-8') as f:
        f.write(client_script)
    
    print("Created test_api_client.py")

def main():
    """Main setup function"""
    
    print("FastAPI Setup for Trading Platform")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("src").exists():
        print("Please run this script from the trading_platform directory")
        return
    
    # Install dependencies
    install_dependencies()
    
    # Create directory structure
    create_api_structure()
    
    # Create startup script
    create_startup_script()
    
    # Update requirements
    create_requirements_update()
    
    # Create test client
    create_example_client()
    
    print("\\n" + "=" * 50)
    print("FastAPI setup complete!")
    print("\\nNext steps:")
    print("1. Copy the API files (main.py, routes, schemas) to their locations")
    print("2. Run: python start_api.py")
    print("3. Visit: http://localhost:8000/docs for API documentation")
    print("4. Test with: python test_api_client.py")
    print("\\nYour trading platform API will be ready!")

if __name__ == "__main__":
    main()