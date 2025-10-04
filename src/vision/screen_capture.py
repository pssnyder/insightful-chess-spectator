"""
Screen capture functionality for the Chess Spectator.
Handles capturing screenshots from specific windows and applications.
"""

import asyncio
import time
from typing import Optional, List, Tuple
import numpy as np
import cv2
import pygetwindow as gw
import pyautogui
import mss
from dataclasses import dataclass
import logging

from ..config.settings import VisionConfig

@dataclass
class WindowInfo:
    """Information about a captured window."""
    title: str
    process_name: str
    position: Tuple[int, int, int, int]  # x, y, width, height
    is_chess_platform: bool = False
    platform_type: Optional[str] = None  # "chess.com", "lichess", "arena", etc.

class ScreenCapture:
    """Handles screen capture and window management."""
    
    def __init__(self, config: VisionConfig):
        self.config = config
        self.logger = logging.getLogger("chess_spectator.vision.capture")
        
        # Known chess platforms
        self.chess_platforms = {
            "chess.com": ["chess.com", "chess"],
            "lichess.org": ["lichess", "lichess.org"],
            "arena": ["arena chess", "arena"],
            "chessbase": ["chessbase", "fritz"],
            "chess24": ["chess24"],
        }
        
        # Currently selected window
        self.selected_window: Optional[WindowInfo] = None
        
        # MSS for efficient screen capture
        self.sct = mss.mss()
    
    async def get_available_windows(self) -> List[WindowInfo]:
        """Get list of available windows that might contain chess games."""
        windows = []
        
        try:
            # Get all visible windows
            all_windows = gw.getAllWindows()
            
            for window in all_windows:
                if window.title and len(window.title.strip()) > 0:
                    # Basic window info
                    window_info = WindowInfo(
                        title=window.title,
                        process_name="unknown",  # We'll improve this later
                        position=(window.left, window.top, window.width, window.height)
                    )
                    
                    # Check if it's a chess platform
                    window_info.is_chess_platform, window_info.platform_type = self._identify_chess_platform(window.title)
                    
                    windows.append(window_info)
                    
        except Exception as e:
            self.logger.error(f"Error getting window list: {e}")
        
        return windows
    
    def _identify_chess_platform(self, window_title: str) -> Tuple[bool, Optional[str]]:
        """Identify if a window contains a chess platform."""
        title_lower = window_title.lower()
        
        for platform, keywords in self.chess_platforms.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return True, platform
        
        # Check for browser windows that might have chess sites
        browser_keywords = ["chrome", "firefox", "edge", "safari", "opera"]
        for browser in browser_keywords:
            if browser in title_lower:
                # Could be a chess site in browser
                return True, "browser"
        
        return False, None
    
    async def select_window(self, window_info: WindowInfo) -> bool:
        """Select a window for capture."""
        try:
            self.selected_window = window_info
            self.logger.info(f"Selected window: {window_info.title}")
            return True
        except Exception as e:
            self.logger.error(f"Error selecting window: {e}")
            return False
    
    async def capture_selected_window(self) -> Optional[np.ndarray]:
        """Capture the currently selected window."""
        if not self.selected_window:
            self.logger.warning("No window selected for capture")
            return None
        
        try:
            # Get window position
            x, y, width, height = self.selected_window.position
            
            # Capture using mss for better performance
            monitor = {
                "top": y,
                "left": x,
                "width": width,
                "height": height
            }
            
            screenshot = self.sct.grab(monitor)
            
            # Convert to numpy array
            img_array = np.array(screenshot)
            
            # Convert from BGRA to BGR (remove alpha channel)
            if img_array.shape[2] == 4:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
            
            return img_array
            
        except Exception as e:
            self.logger.error(f"Error capturing window: {e}")
            return None
    
    async def capture_full_screen(self) -> Optional[np.ndarray]:
        """Capture the full screen."""
        try:
            # Use pyautogui for full screen capture
            screenshot = pyautogui.screenshot()
            
            # Convert to numpy array and BGR format
            img_array = np.array(screenshot)
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            return img_array
            
        except Exception as e:
            self.logger.error(f"Error capturing full screen: {e}")
            return None
    
    async def auto_detect_chess_window(self) -> Optional[WindowInfo]:
        """Automatically detect and select a chess window."""
        windows = await self.get_available_windows()
        
        # Priority order for auto-selection
        priority_platforms = ["chess.com", "lichess.org", "arena", "chessbase"]
        
        # First, try to find known chess platforms
        for platform in priority_platforms:
            for window in windows:
                if window.platform_type == platform:
                    await self.select_window(window)
                    return window
        
        # Then try browser windows (might have chess sites)
        for window in windows:
            if window.platform_type == "browser":
                await self.select_window(window)
                return window
        
        # Finally, try any window marked as chess platform
        for window in windows:
            if window.is_chess_platform:
                await self.select_window(window)
                return window
        
        self.logger.warning("No chess window detected for auto-selection")
        return None
    
    def get_capture_region(self, x_percent: float = 0.1, y_percent: float = 0.1, 
                          width_percent: float = 0.8, height_percent: float = 0.8) -> Tuple[int, int, int, int]:
        """Get a sub-region of the selected window for capture."""
        if not self.selected_window:
            return (0, 0, 100, 100)
        
        x, y, width, height = self.selected_window.position
        
        # Calculate sub-region
        sub_x = int(x + width * x_percent)
        sub_y = int(y + height * y_percent)
        sub_width = int(width * width_percent)
        sub_height = int(height * height_percent)
        
        return (sub_x, sub_y, sub_width, sub_height)
    
    async def cleanup(self):
        """Cleanup screen capture resources."""
        try:
            if hasattr(self, 'sct'):
                self.sct.close()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")