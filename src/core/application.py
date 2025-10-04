"""
Main application class for the Insightful Chess Spectator.
Coordinates all components and manages the application lifecycle.
"""

import asyncio
import time
from typing import Optional, Dict, Any
import logging
from dataclasses import dataclass

from ..config.settings import AppConfig
from ..vision.board_detector import BoardDetector
from ..vision.screen_capture import ScreenCapture
from ..analysis.chess_engine import ChessAnalyzer
from ..analysis.position_evaluator import PositionEvaluator
from ..ai.commentary_generator import CommentaryGenerator
from ..security.anti_cheat import AntiCheatMonitor
from ..ui.main_window import SpectatorUI
from ..utils.logger import SecurityLogger, PerformanceLogger

@dataclass
class GameState:
    """Current state of the chess game being analyzed."""
    board_fen: Optional[str] = None
    last_move: Optional[str] = None
    analysis_ready: bool = False
    analysis_timestamp: Optional[float] = None
    commentary: Optional[str] = None
    window_info: Optional[Dict[str, Any]] = None

class ChessSpectatorApp:
    """Main application class for the Chess Spectator."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger("chess_spectator.app")
        self.security_logger = SecurityLogger(self.logger)
        self.performance_logger = PerformanceLogger(self.logger)
        
        # Application state
        self.running = False
        self.game_state = GameState()
        self.last_analysis_time = 0
        
        # Initialize components
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialize all application components."""
        try:
            # Core components
            self.screen_capture = ScreenCapture(self.config.vision)
            self.board_detector = BoardDetector(self.config.vision)
            self.chess_analyzer = ChessAnalyzer(self.config.analysis)
            self.position_evaluator = PositionEvaluator()
            self.commentary_generator = CommentaryGenerator(self.config.firebase)
            
            # Security components
            self.anti_cheat = AntiCheatMonitor(self.config.anti_cheat)
            
            # UI components
            self.ui = SpectatorUI(
                config=self.config.ui,
                on_start_callback=self._start_analysis,
                on_stop_callback=self._stop_analysis,
                on_settings_callback=self._show_settings
            )
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    async def run(self):
        """Main application run loop."""
        self.logger.info("Starting Chess Spectator application")
        self.running = True
        
        try:
            # Start UI in main thread
            await self._run_ui_loop()
            
        except Exception as e:
            self.logger.error(f"Application error: {e}")
        finally:
            await self._cleanup()
    
    async def _run_ui_loop(self):
        """Run the UI event loop."""
        self.ui.start()
        
        while self.running:
            # Update UI
            self.ui.update()
            
            # Process analysis if active
            if self.game_state.analysis_ready:
                await self._process_analysis()
            
            # Small delay to prevent excessive CPU usage
            await asyncio.sleep(0.1)
    
    async def _start_analysis(self):
        """Start chess game analysis."""
        self.logger.info("Starting chess analysis")
        
        # Perform security checks
        security_check = await self.anti_cheat.perform_security_check()
        if not security_check.passed:
            self.logger.warning(f"Security check failed: {security_check.reason}")
            self.ui.show_error(f"Security Check Failed: {security_check.reason}")
            return
        
        # Start analysis loop
        self.game_state.analysis_ready = True
        self.ui.update_status("Analysis Active")
        
    async def _stop_analysis(self):
        """Stop chess game analysis."""
        self.logger.info("Stopping chess analysis")
        self.game_state.analysis_ready = False
        self.ui.update_status("Analysis Stopped")
        
    async def _process_analysis(self):
        """Process a single analysis cycle."""
        try:
            start_time = time.time()
            
            # Capture screen
            screenshot = await self.screen_capture.capture_selected_window()
            if screenshot is None:
                return
            
            # Detect chess board
            board_info = await self.board_detector.detect_board(screenshot)
            if board_info is None:
                return
            
            # Check if position has changed
            current_fen = board_info.fen
            if current_fen == self.game_state.board_fen:
                return  # No change in position
            
            # Security: Enforce analysis delay
            current_time = time.time()
            time_since_last = current_time - self.last_analysis_time
            if time_since_last < self.config.anti_cheat.min_analysis_delay:
                remaining_delay = self.config.anti_cheat.min_analysis_delay - time_since_last
                self.security_logger.log_analysis_delay(remaining_delay)
                await asyncio.sleep(remaining_delay)
            
            # Update game state
            self.game_state.board_fen = current_fen
            self.last_analysis_time = time.time()
            
            # Analyze position
            analysis = await self.chess_analyzer.analyze_position(current_fen)
            if analysis is None:
                return
            
            # Evaluate position qualitatively
            evaluation = self.position_evaluator.evaluate_position(current_fen, analysis)
            
            # Generate commentary
            commentary = await self.commentary_generator.generate_commentary(
                fen=current_fen,
                analysis=analysis,
                evaluation=evaluation
            )
            
            # Update UI
            self.game_state.commentary = commentary
            self.ui.update_analysis(
                board_fen=current_fen,
                evaluation=evaluation,
                commentary=commentary
            )
            
            # Log performance
            processing_time = time.time() - start_time
            self.performance_logger.log_vision_performance(processing_time, True)
            
        except Exception as e:
            self.logger.error(f"Analysis processing error: {e}")
            self.performance_logger.log_vision_performance(time.time() - start_time, False)
    
    async def _show_settings(self):
        """Show application settings dialog."""
        self.ui.show_settings_dialog(self.config)
    
    async def _cleanup(self):
        """Cleanup resources on application shutdown."""
        self.logger.info("Cleaning up application resources")
        self.running = False
        
        try:
            if hasattr(self, 'chess_analyzer'):
                await self.chess_analyzer.cleanup()
            
            if hasattr(self, 'commentary_generator'):
                await self.commentary_generator.cleanup()
                
            if hasattr(self, 'ui'):
                self.ui.cleanup()
                
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
        
        self.logger.info("Application cleanup complete")