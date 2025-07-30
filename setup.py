#!/usr/bin/env python3
"""
Simple setup script without emojis - guaranteed to work on Windows
"""

import os
import shutil
from pathlib import Path

def create_directory_structure():
    """Create the complete directory structure for the trading platform"""
    
    base_dir = Path("trading_platform")
    
    directories = [
        "src/data_generation",
        "src/pricing", 
        "src/portfolio",
        "src/database",
        "src/database/migrations",
        "src/api",
        "src/api/routes",
        "src/api/middleware", 
        "src/api/schemas",
        "src/utils",
        "data/market_data/batch",
        "data/market_data/live", 
        "data/databases",
        "data/exports",
        "tests/test_data_generation",
        "tests/test_pricing",
        "tests/test_portfolio", 
        "tests/test_integration",
        "scripts/demo",
        "docs",
        "deployment/docker",
        "deployment/nginx",
        "deployment/scripts",
        "analysis/notebooks",
        "analysis/reports",
        "analysis/visualizations",
        "frontend/src/components/market",
        "frontend/src/components/portfolio", 
        "frontend/src/components/trading",
        "frontend/src/components/charts",
        "frontend/src/pages",
        "frontend/src/hooks",
        "frontend/src/utils",
        "frontend/public",
        "frontend/build",
        "logs"
    ]
    
    print("Creating trading platform directory structure...")
    
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {dir_path}")
    
    return base_dir

def create_init_files(base_dir):
    """Create __init__.py files for Python packages"""
    
    init_locations = [
        "src",
        "src/data_generation",
        "src/pricing",
        "src/portfolio", 
        "src/database",
        "src/database/migrations",
        "src/api",
        "src/api/routes",
        "src/api/middleware",
        "src/api/schemas", 
        "src/utils",
        "tests",
        "tests/test_data_generation",
        "tests/test_pricing",
        "tests/test_portfolio",
        "tests/test_integration"
    ]
    
    print("Creating __init__.py files...")
    
    for location in init_locations:
        init_path = base_dir / location / "__init__.py"
        init_path.touch()
        print(f"Created: {init_path}")

def create_requirements_txt(base_dir):
    """Create requirements.txt file"""
    
    requirements_content = """# Core data processing
pandas>=1.5.0
numpy>=1.24.0

# Web framework
fastapi>=0.100.0
uvicorn>=0.22.0
python-multipart>=0.0.6

# Data validation
pydantic>=2.0.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0

# Analysis and visualization  
jupyter>=1.0.0
matplotlib>=3.7.0
plotly>=5.15.0
seaborn>=0.12.0

# Utilities
python-dotenv>=1.0.0
click>=8.0.0

# Development
black>=23.0.0
flake8>=6.0.0
mypy>=1.5.0
"""
    
    req_path = base_dir / "requirements.txt"
    with open(req_path, 'w', encoding='utf-8') as f:
        f.write(requirements_content)
    
    print(f"Created: {req_path}")

def migrate_existing_files(base_dir):
    """Migrate existing project files to new structure"""
    
    file_migrations = {
        "price-logic.py": "src/pricing/option_pricing.py",
        "valid-num-engine.py": "src/data_generation/batch_generator.py", 
        "portfolio-classes.py": "src/portfolio/portfolio_manager.py"
    }
    
    print("Migrating existing files...")
    
    for old_file, new_location in file_migrations.items():
        if os.path.exists(old_file):
            new_path = base_dir / new_location
            shutil.copy2(old_file, new_path)
            print(f"Migrated: {old_file} -> {new_path}")
        else:
            print(f"File not found: {old_file} (skipping)")

def create_placeholder_files(base_dir):
    """Create placeholder files to maintain directory structure"""
    
    placeholder_files = [
        "data/market_data/.gitkeep",
        "data/databases/.gitkeep", 
        "data/exports/.gitkeep",
        "logs/.gitkeep"
    ]
    
    for placeholder in placeholder_files:
        placeholder_path = base_dir / placeholder
        placeholder_path.touch()

def main():
    """Main setup function"""
    
    print("Trading Platform Setup")
    print("=" * 40)
    
    # Create directory structure
    base_dir = create_directory_structure()
    
    # Create Python package files
    create_init_files(base_dir)
    
    # Create configuration files
    create_requirements_txt(base_dir)
    
    # Create placeholder files
    create_placeholder_files(base_dir)
    
    # Migrate existing files
    migrate_existing_files(base_dir)
    
    print("Setup complete!")
    print(f"Project created in: {base_dir.absolute()}")
    print("Next steps:")
    print(f"1. cd {base_dir}")
    print("2. pip install -r requirements.txt")
    print("3. Start developing!")

if __name__ == "__main__":
    main()