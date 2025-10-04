"""
Main entry point for the Insightful Chess Spectator application.
Provides real-time chess analysis with integrity-focused design.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.application import ChessSpectatorApp
from src.utils.logger import setup_logger
from src.config.settings import load_config

def main():
    """Main application entry point."""
    # Setup logging
    logger = setup_logger()
    logger.info("Starting Insightful Chess Spectator...")
    
    try:
        # Load configuration
        config = load_config()
        
        # Initialize and run application
        app = ChessSpectatorApp(config)
        asyncio.run(app.run())
        
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
    finally:
        logger.info("Chess Spectator shutdown complete")

if __name__ == "__main__":
    main()