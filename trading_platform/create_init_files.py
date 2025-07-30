#!/usr/bin/env python3
"""
Script to create all missing __init__.py files
Save this as: trading_platform/create_init_files.py
"""

import os
from pathlib import Path

def create_init_files():
    """Create all necessary __init__.py files for the project"""
    
    print("Creating __init__.py Files")
    print("=" * 40)
    
    # Get the current directory (should be trading_platform)
    current_dir = Path.cwd()
    print(f"Working in: {current_dir}")
    
    # List of all directories that need __init__.py files
    directories_needing_init = [
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
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in directories_needing_init:
        full_dir_path = current_dir / dir_path
        init_file_path = full_dir_path / "__init__.py"
        
        # Check if directory exists
        if not full_dir_path.exists():
            print(f"⚠ Directory doesn't exist: {dir_path} (skipping)")
            skipped_count += 1
            continue
        
        # Check if __init__.py already exists
        if init_file_path.exists():
            print(f"✓ Already exists: {dir_path}/__init__.py")
            skipped_count += 1
            continue
        
        # Create the __init__.py file
        try:
            # Create empty __init__.py file
            init_file_path.touch()
            print(f"✅ Created: {dir_path}/__init__.py")
            created_count += 1
            
        except Exception as e:
            print(f"❌ Failed to create {dir_path}/__init__.py: {e}")
    
    print(f"\nSummary:")
    print(f"  Created: {created_count} files")
    print(f"  Skipped: {skipped_count} files")
    
    return created_count

def create_missing_directories():
    """Create any missing directories first"""
    
    print("\nCreating Missing Directories")
    print("=" * 40)
    
    current_dir = Path.cwd()
    
    # Essential directories for the project
    essential_directories = [
        "src",
        "src/data_generation",
        "src/pricing", 
        "src/portfolio",
        "src/utils",
        "scripts",
        "data",
        "data/market_data",
        "logs"
    ]
    
    created_count = 0
    
    for dir_path in essential_directories:
        full_dir_path = current_dir / dir_path
        
        if not full_dir_path.exists():
            try:
                full_dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {dir_path}")
                created_count += 1
            except Exception as e:
                print(f"❌ Failed to create directory {dir_path}: {e}")
        else:
            print(f"✓ Directory exists: {dir_path}")
    
    print(f"\nCreated {created_count} directories")
    return created_count

def verify_structure():
    """Verify the final structure"""
    
    print("\nVerifying Project Structure")
    print("=" * 40)
    
    current_dir = Path.cwd()
    
    # Key files that should exist for the project to work
    key_files = [
        "src/__init__.py",
        "src/data_generation/__init__.py", 
        "src/pricing/__init__.py",
        "src/portfolio/__init__.py"
    ]
    
    all_good = True
    
    for file_path in key_files:
        full_path = current_dir / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            all_good = False
    
    if all_good:
        print(f"\n🎉 All essential __init__.py files are in place!")
        print(f"You can now run your scripts without import errors.")
    else:
        print(f"\n⚠ Some files are still missing. Please check the errors above.")
    
    return all_good

def main():
    """Main function"""
    
    print("Python Package Initialization Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("src").exists() and not Path("trading_platform").exists():
        print("❌ ERROR: This doesn't look like the trading_platform directory")
        print(f"Current directory: {Path.cwd()}")
        print("\nPlease:")
        print("1. Navigate to your trading_platform folder")
        print("2. Run this script from inside trading_platform/")
        return False
    
    # If we're in the parent directory, try to enter trading_platform
    if Path("trading_platform").exists() and not Path("src").exists():
        print("Detected trading_platform subdirectory. Changing to it...")
        os.chdir("trading_platform")
        print(f"Now in: {Path.cwd()}")
    
    try:
        # Step 1: Create missing directories
        create_missing_directories()
        
        # Step 2: Create __init__.py files
        created_files = create_init_files()
        
        # Step 3: Verify everything is in place
        success = verify_structure()
        
        if success:
            print(f"\n🚀 Setup Complete!")
            print(f"You can now try running:")
            print(f"  python scripts/quick_start.py")
        else:
            print(f"\n⚠ Setup incomplete. Please check the missing files above.")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n✅ All done! Your import errors should now be fixed.")
    else:
        print(f"\n❌ Setup failed. Please check the errors above and try again.")
    
    # Pause so user can see the results
    input("\nPress Enter to exit...")