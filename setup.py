"""
Setup script for the Insightful Chess Spectator.
Downloads required models and configures the application.
"""

import os
import sys
import subprocess
from pathlib import Path
import requests
import zipfile
import logging

def setup_logging():
    """Setup logging for the setup process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('setup')

def create_directories():
    """Create necessary directories."""
    directories = [
        'data',
        'models', 
        'logs',
        'config',
        'engines'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✓ Created necessary directories")

def download_stockfish():
    """Download Stockfish chess engine if not present."""
    stockfish_path = Path("engines/stockfish.exe")
    
    if stockfish_path.exists():
        print("✓ Stockfish already installed")
        return
    
    print("Downloading Stockfish chess engine...")
    
    # URLs for different platforms
    urls = {
        'windows': 'https://stockfishchess.org/files/stockfish_15_win_x64_avx2.zip',
        'linux': 'https://stockfishchess.org/files/stockfish_15_linux_x64_avx2.zip',
        'darwin': 'https://stockfishchess.org/files/stockfish_15_mac.zip'
    }
    
    platform = sys.platform
    if platform.startswith('win'):
        platform = 'windows'
    elif platform.startswith('linux'):
        platform = 'linux'
    elif platform.startswith('darwin'):
        platform = 'darwin'
    else:
        print(f"⚠️  Unsupported platform: {platform}")
        print("Please manually install Stockfish and ensure it's in your PATH")
        return
    
    try:
        url = urls[platform]
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        zip_path = Path("engines/stockfish.zip")
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extract the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("engines/")
        
        # Remove the zip file
        zip_path.unlink()
        
        print("✓ Stockfish downloaded and installed")
        
    except Exception as e:
        print(f"⚠️  Failed to download Stockfish: {e}")
        print("Please manually install Stockfish from https://stockfishchess.org/")

def install_python_packages():
    """Install required Python packages."""
    print("Installing Python packages...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✓ Python packages installed")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Failed to install packages: {e}")
        print("Please run: pip install -r requirements.txt")

def create_env_file():
    """Create .env file from example if it doesn't exist."""
    env_path = Path(".env")
    example_path = Path(".env.example")
    
    if not env_path.exists() and example_path.exists():
        import shutil
        shutil.copy(example_path, env_path)
        print("✓ Created .env file from example")
        print("Please edit .env with your Firebase configuration")
    else:
        print("✓ .env file already exists")

def verify_installation():
    """Verify that the installation is working."""
    print("\nVerifying installation...")
    
    try:
        # Try importing main modules
        import cv2
        import chess
        import numpy as np
        print("✓ Core dependencies available")
        
        # Check if Stockfish is accessible
        from stockfish import Stockfish
        try:
            engine = Stockfish()
            print("✓ Stockfish engine accessible")
        except Exception:
            print("⚠️  Stockfish not found in PATH - please check installation")
        
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your Firebase configuration")
        print("2. Run: python main.py")
        
    except ImportError as e:
        print(f"⚠️  Missing dependency: {e}")
        print("Please install missing packages with: pip install -r requirements.txt")

def main():
    """Main setup function."""
    logger = setup_logging()
    
    print("🏁 Setting up Insightful Chess Spectator...")
    print("=" * 50)
    
    try:
        create_directories()
        install_python_packages()
        download_stockfish()
        create_env_file()
        verify_installation()
        
    except KeyboardInterrupt:
        print("\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()