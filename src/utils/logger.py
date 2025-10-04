"""
Logging utilities for the Chess Spectator application.
Provides structured logging with different levels and output formats.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

def setup_logger(
    name: str = "chess_spectator",
    level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Setup a logger with both console and file output.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        console_output: Whether to output to console
    
    Returns:
        Configured logger instance
    """
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        # Default log file
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d")
        default_log_file = log_dir / f"chess_spectator_{timestamp}.log"
        
        file_handler = logging.FileHandler(default_log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent duplicate messages
    logger.propagate = False
    
    return logger

class SecurityLogger:
    """Specialized logger for security and anti-cheat events."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
    def log_window_detection(self, window_title: str, process_name: str) -> None:
        """Log window detection for anti-cheat monitoring."""
        self.logger.info(f"SECURITY: Window detected - Title: {window_title}, Process: {process_name}")
        
    def log_analysis_delay(self, delay_seconds: float) -> None:
        """Log analysis delay enforcement."""
        self.logger.info(f"SECURITY: Analysis delay enforced - {delay_seconds}s")
        
    def log_rate_limit(self, client_id: str, request_count: int) -> None:
        """Log rate limiting events."""
        self.logger.warning(f"SECURITY: Rate limit triggered - Client: {client_id}, Requests: {request_count}")
        
    def log_suspicious_activity(self, activity_type: str, details: str) -> None:
        """Log suspicious activity."""
        self.logger.warning(f"SECURITY: Suspicious activity - Type: {activity_type}, Details: {details}")
        
    def log_live_game_detection(self, platform: str, game_id: str) -> None:
        """Log live game detection."""
        self.logger.warning(f"SECURITY: Live game detected - Platform: {platform}, Game: {game_id}")

class PerformanceLogger:
    """Logger for performance monitoring."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
    def log_vision_performance(self, processing_time: float, success: bool) -> None:
        """Log computer vision performance."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"PERFORMANCE: Vision processing - {processing_time:.3f}s - {status}")
        
    def log_analysis_performance(self, depth: int, time_taken: float, positions_evaluated: int) -> None:
        """Log chess analysis performance."""
        self.logger.info(f"PERFORMANCE: Analysis - Depth: {depth}, Time: {time_taken:.3f}s, Positions: {positions_evaluated}")
        
    def log_ai_response_time(self, service: str, response_time: float) -> None:
        """Log AI service response times."""
        self.logger.info(f"PERFORMANCE: AI Response - Service: {service}, Time: {response_time:.3f}s")