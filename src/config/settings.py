"""
Configuration and settings management for the Chess Spectator.
Handles loading of environment variables, Firebase config, and application settings.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class AntiCheatConfig:
    """Anti-cheating configuration settings."""
    min_analysis_delay: float = 30.0  # Minimum delay in seconds before showing analysis
    spectator_mode_only: bool = True
    rate_limit_requests: int = 10  # Max requests per minute
    require_window_detection: bool = True
    block_live_games: bool = True  # Block analysis of live games being played by user

@dataclass
class VisionConfig:
    """Computer vision configuration for board detection."""
    board_detection_confidence: float = 0.8
    piece_detection_confidence: float = 0.7
    square_size_min: int = 30
    square_size_max: int = 100
    color_tolerance: int = 30
    
@dataclass
class AnalysisConfig:
    """Chess analysis configuration."""
    stockfish_depth: int = 15
    stockfish_time: float = 1.0
    max_variations: int = 3
    evaluation_threshold: float = 0.5  # Centipawn threshold for "significant" moves
    
@dataclass
class FirebaseConfig:
    """Firebase AI service configuration."""
    project_id: str = ""
    credentials_path: str = ""
    collection_name: str = "chess_analysis"
    
@dataclass
class UIConfig:
    """User interface configuration."""
    window_width: int = 1200
    window_height: int = 800
    update_interval: int = 1000  # milliseconds
    commentary_max_length: int = 500
    
@dataclass
class AppConfig:
    """Main application configuration."""
    # Sub-configurations (must be before fields with defaults)
    anti_cheat: AntiCheatConfig
    vision: VisionConfig
    analysis: AnalysisConfig
    firebase: FirebaseConfig
    ui: UIConfig
    
    # Basic settings
    debug_mode: bool = False
    log_level: str = "INFO"
    data_dir: str = "./data"
    models_dir: str = "./models"
    
    def __post_init__(self):
        """Ensure data directories exist."""
        Path(self.data_dir).mkdir(exist_ok=True)
        Path(self.models_dir).mkdir(exist_ok=True)

def load_config() -> AppConfig:
    """Load configuration from environment variables and config files."""
    
    # Load from environment variables
    config = AppConfig(
        debug_mode=os.getenv("DEBUG", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        data_dir=os.getenv("DATA_DIR", "./data"),
        models_dir=os.getenv("MODELS_DIR", "./models"),
        
        anti_cheat=AntiCheatConfig(
            min_analysis_delay=float(os.getenv("MIN_ANALYSIS_DELAY", "30.0")),
            spectator_mode_only=os.getenv("SPECTATOR_MODE_ONLY", "true").lower() == "true",
            rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "10")),
            require_window_detection=os.getenv("REQUIRE_WINDOW_DETECTION", "true").lower() == "true",
            block_live_games=os.getenv("BLOCK_LIVE_GAMES", "true").lower() == "true"
        ),
        
        vision=VisionConfig(
            board_detection_confidence=float(os.getenv("BOARD_DETECTION_CONFIDENCE", "0.8")),
            piece_detection_confidence=float(os.getenv("PIECE_DETECTION_CONFIDENCE", "0.7")),
            square_size_min=int(os.getenv("SQUARE_SIZE_MIN", "30")),
            square_size_max=int(os.getenv("SQUARE_SIZE_MAX", "100")),
            color_tolerance=int(os.getenv("COLOR_TOLERANCE", "30"))
        ),
        
        analysis=AnalysisConfig(
            stockfish_depth=int(os.getenv("STOCKFISH_DEPTH", "15")),
            stockfish_time=float(os.getenv("STOCKFISH_TIME", "1.0")),
            max_variations=int(os.getenv("MAX_VARIATIONS", "3")),
            evaluation_threshold=float(os.getenv("EVALUATION_THRESHOLD", "0.5"))
        ),
        
        firebase=FirebaseConfig(
            project_id=os.getenv("FIREBASE_PROJECT_ID", ""),
            credentials_path=os.getenv("FIREBASE_CREDENTIALS_PATH", ""),
            collection_name=os.getenv("FIREBASE_COLLECTION", "chess_analysis")
        ),
        
        ui=UIConfig(
            window_width=int(os.getenv("WINDOW_WIDTH", "1200")),
            window_height=int(os.getenv("WINDOW_HEIGHT", "800")),
            update_interval=int(os.getenv("UPDATE_INTERVAL", "1000")),
            commentary_max_length=int(os.getenv("COMMENTARY_MAX_LENGTH", "500"))
        )
    )
    
    # Load config file if it exists
    config_file = Path("config.json")
    if config_file.exists():
        with open(config_file, 'r') as f:
            file_config = json.load(f)
            # Merge file config with environment config
            # Environment variables take precedence
    
    return config

def save_config(config: AppConfig, path: str = "config.json") -> None:
    """Save configuration to a JSON file."""
    config_dict = {
        "debug_mode": config.debug_mode,
        "log_level": config.log_level,
        "data_dir": config.data_dir,
        "models_dir": config.models_dir,
        "anti_cheat": {
            "min_analysis_delay": config.anti_cheat.min_analysis_delay,
            "spectator_mode_only": config.anti_cheat.spectator_mode_only,
            "rate_limit_requests": config.anti_cheat.rate_limit_requests,
            "require_window_detection": config.anti_cheat.require_window_detection,
            "block_live_games": config.anti_cheat.block_live_games
        },
        "vision": {
            "board_detection_confidence": config.vision.board_detection_confidence,
            "piece_detection_confidence": config.vision.piece_detection_confidence,
            "square_size_min": config.vision.square_size_min,
            "square_size_max": config.vision.square_size_max,
            "color_tolerance": config.vision.color_tolerance
        },
        "analysis": {
            "stockfish_depth": config.analysis.stockfish_depth,
            "stockfish_time": config.analysis.stockfish_time,
            "max_variations": config.analysis.max_variations,
            "evaluation_threshold": config.analysis.evaluation_threshold
        },
        "firebase": {
            "project_id": config.firebase.project_id,
            "credentials_path": config.firebase.credentials_path,
            "collection_name": config.firebase.collection_name
        },
        "ui": {
            "window_width": config.ui.window_width,
            "window_height": config.ui.window_height,
            "update_interval": config.ui.update_interval,
            "commentary_max_length": config.ui.commentary_max_length
        }
    }
    
    with open(path, 'w') as f:
        json.dump(config_dict, f, indent=2)