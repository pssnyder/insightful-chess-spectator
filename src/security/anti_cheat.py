"""
Anti-cheat and security monitoring for the Chess Spectator.
Implements various measures to prevent abuse and maintain game integrity.
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import hashlib
import logging
import psutil
import re

from ..config.settings import AntiCheatConfig
from ..utils.logger import SecurityLogger

@dataclass
class SecurityCheck:
    """Result of a security check."""
    passed: bool
    reason: str
    risk_level: str  # "low", "medium", "high"
    timestamp: float
    details: Optional[Dict[str, Any]] = None

@dataclass
class WindowAnalysis:
    """Analysis of a detected window."""
    title: str
    process_name: str
    is_chess_platform: bool
    platform_type: str
    is_live_game: bool
    confidence: float

class AntiCheatMonitor:
    """Monitors for potential cheating and abuse scenarios."""
    
    def __init__(self, config: AntiCheatConfig):
        self.config = config
        self.logger = logging.getLogger("chess_spectator.security.anticheat")
        self.security_logger = SecurityLogger(self.logger)
        
        # Tracking variables
        self.analysis_history: List[Dict[str, Any]] = []
        self.last_analysis_time = 0
        self.request_count = 0
        self.request_window_start = time.time()
        
        # Known chess platforms and their indicators
        self.chess_platforms = {
            "chess.com": {
                "url_patterns": [r"chess\.com", r"www\.chess\.com"],
                "title_patterns": [r"chess\.com", r"play chess", r"vs\.", r"game review"],
                "live_indicators": [r"playing", r"game", r"move", r"time", r"vs\."],
                "spectator_indicators": [r"watching", r"analysis", r"review", r"game review"]
            },
            "lichess.org": {
                "url_patterns": [r"lichess\.org"],
                "title_patterns": [r"lichess", r"free online chess"],
                "live_indicators": [r"playing", r"bullet", r"blitz", r"rapid"],
                "spectator_indicators": [r"analysis", r"study", r"watching", r"tv"]
            },
            "arena": {
                "title_patterns": [r"arena chess", r"arena", r"chess gui"],
                "live_indicators": [r"thinking", r"move", r"time"],
                "spectator_indicators": [r"analysis", r"reviewing", r"engine"]
            }
        }
        
        # Risk assessment weights
        self.risk_weights = {
            "live_game_detected": 10,
            "rapid_analysis_requests": 5,
            "suspicious_window_activity": 7,
            "rate_limit_exceeded": 8,
            "unknown_chess_platform": 3,
            "multiple_chess_windows": 4
        }
    
    async def perform_security_check(self) -> SecurityCheck:
        """Perform comprehensive security check."""
        start_time = time.time()
        risks = []
        risk_score = 0
        
        try:
            # Check 1: Analysis delay enforcement
            delay_check = await self._check_analysis_delay()
            if not delay_check['passed']:
                risks.append(delay_check)
                risk_score += self.risk_weights.get(delay_check['type'], 5)
            
            # Check 2: Rate limiting
            rate_check = await self._check_rate_limiting()
            if not rate_check['passed']:
                risks.append(rate_check)
                risk_score += self.risk_weights.get(rate_check['type'], 5)
            
            # Check 3: Window analysis
            window_check = await self._analyze_active_windows()
            if not window_check['passed']:
                risks.append(window_check)
                risk_score += self.risk_weights.get(window_check['type'], 5)
            
            # Check 4: Live game detection
            live_game_check = await self._detect_live_games()
            if not live_game_check['passed']:
                risks.append(live_game_check)
                risk_score += self.risk_weights.get(live_game_check['type'], 10)
            
            # Check 5: Process analysis
            process_check = await self._analyze_running_processes()
            if not process_check['passed']:
                risks.append(process_check)
                risk_score += self.risk_weights.get(process_check['type'], 3)
            
            # Determine overall result
            passed = risk_score < 15  # Threshold for blocking
            
            if risk_score >= 20:
                risk_level = "high"
            elif risk_score >= 10:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            reason = self._generate_security_reason(risks, passed)
            
            # Log security event
            if not passed:
                self.security_logger.log_suspicious_activity(
                    "Security Check Failed", 
                    f"Risk score: {risk_score}, Risks: {[r['type'] for r in risks]}"
                )
            
            return SecurityCheck(
                passed=passed,
                reason=reason,
                risk_level=risk_level,
                timestamp=start_time,
                details={
                    'risk_score': risk_score,
                    'risks': risks,
                    'check_duration': time.time() - start_time
                }
            )
            
        except Exception as e:
            self.logger.error(f"Security check error: {e}")
            return SecurityCheck(
                passed=False,
                reason="Security check failed due to internal error",
                risk_level="high",
                timestamp=start_time
            )
    
    async def _check_analysis_delay(self) -> Dict[str, Any]:
        """Check if minimum analysis delay is being enforced."""
        current_time = time.time()
        time_since_last = current_time - self.last_analysis_time
        
        if self.last_analysis_time > 0 and time_since_last < self.config.min_analysis_delay:
            self.security_logger.log_analysis_delay(self.config.min_analysis_delay - time_since_last)
            return {
                'passed': False,
                'type': 'rapid_analysis_requests',
                'details': f'Analysis requested too quickly: {time_since_last:.1f}s < {self.config.min_analysis_delay}s'
            }
        
        self.last_analysis_time = current_time
        return {'passed': True, 'type': 'analysis_delay_check'}
    
    async def _check_rate_limiting(self) -> Dict[str, Any]:
        """Check if rate limiting is being respected."""
        current_time = time.time()
        
        # Reset window if needed (1 minute windows)
        if current_time - self.request_window_start > 60:
            self.request_count = 0
            self.request_window_start = current_time
        
        self.request_count += 1
        
        if self.request_count > self.config.rate_limit_requests:
            self.security_logger.log_rate_limit("spectator_client", self.request_count)
            return {
                'passed': False,
                'type': 'rate_limit_exceeded',
                'details': f'Rate limit exceeded: {self.request_count} > {self.config.rate_limit_requests}'
            }
        
        return {'passed': True, 'type': 'rate_limit_check'}
    
    async def _analyze_active_windows(self) -> Dict[str, Any]:
        """Analyze active windows for suspicious activity."""
        try:
            import pygetwindow as gw
            windows = gw.getAllWindows()
            
            chess_windows = []
            suspicious_windows = []
            
            for window in windows:
                if window.title and len(window.title.strip()) > 0:
                    analysis = self._analyze_window(window.title)
                    
                    if analysis.is_chess_platform:
                        chess_windows.append(analysis)
                        
                        if analysis.is_live_game:
                            suspicious_windows.append(analysis)
            
            # Log detected windows
            for analysis in chess_windows:
                self.security_logger.log_window_detection(analysis.title, analysis.process_name)
            
            # Check for concerning patterns
            if len(chess_windows) > 3:
                return {
                    'passed': False,
                    'type': 'multiple_chess_windows',
                    'details': f'Multiple chess windows detected: {len(chess_windows)}'
                }
            
            if suspicious_windows and self.config.block_live_games:
                return {
                    'passed': False,
                    'type': 'live_game_detected',
                    'details': f'Live game windows detected: {[w.title for w in suspicious_windows]}'
                }
            
            return {'passed': True, 'type': 'window_analysis'}
            
        except Exception as e:
            self.logger.error(f"Window analysis error: {e}")
            return {'passed': True, 'type': 'window_analysis_error'}
    
    def _analyze_window(self, window_title: str) -> WindowAnalysis:
        """Analyze a single window title."""
        title_lower = window_title.lower()
        
        # Check each platform
        for platform, patterns in self.chess_platforms.items():
            # Check title patterns
            for pattern in patterns.get('title_patterns', []):
                if re.search(pattern, title_lower):
                    # Determine if it's a live game
                    is_live = False
                    for live_pattern in patterns.get('live_indicators', []):
                        if re.search(live_pattern, title_lower):
                            is_live = True
                            break
                    
                    # If not live, check spectator indicators
                    if not is_live:
                        for spec_pattern in patterns.get('spectator_indicators', []):
                            if re.search(spec_pattern, title_lower):
                                is_live = False
                                break
                    
                    return WindowAnalysis(
                        title=window_title,
                        process_name="unknown",  # Would need additional process detection
                        is_chess_platform=True,
                        platform_type=platform,
                        is_live_game=is_live,
                        confidence=0.8
                    )
        
        # Not a recognized chess platform
        return WindowAnalysis(
            title=window_title,
            process_name="unknown",
            is_chess_platform=False,
            platform_type="unknown",
            is_live_game=False,
            confidence=0.1
        )
    
    async def _detect_live_games(self) -> Dict[str, any]:
        """Detect if user is playing live chess games."""
        try:
            # This would integrate with chess platform APIs to detect live games
            # For now, we rely on window analysis
            
            # Check network activity for chess platform connections
            # This is a simplified check - real implementation would be more sophisticated
            
            return {'passed': True, 'type': 'live_game_detection'}
            
        except Exception as e:
            self.logger.error(f"Live game detection error: {e}")
            return {'passed': True, 'type': 'live_game_detection_error'}
    
    async def _analyze_running_processes(self) -> Dict[str, any]:
        """Analyze running processes for chess engines or suspicious software."""
        try:
            suspicious_processes = []
            chess_engines = ['stockfish', 'komodo', 'leela', 'dragon', 'fritz', 'houdini']
            cheat_indicators = ['cheat', 'hack', 'bot', 'auto']
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name'].lower()
                    
                    # Check for chess engines
                    for engine in chess_engines:
                        if engine in proc_name:
                            suspicious_processes.append(f"Chess engine: {proc.info['name']}")
                    
                    # Check for potential cheat software
                    for indicator in cheat_indicators:
                        if indicator in proc_name:
                            suspicious_processes.append(f"Suspicious: {proc.info['name']}")
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if suspicious_processes:
                self.security_logger.log_suspicious_activity(
                    "Suspicious Processes", 
                    ", ".join(suspicious_processes)
                )
                
                return {
                    'passed': False,
                    'type': 'suspicious_processes',
                    'details': f'Suspicious processes detected: {suspicious_processes}'
                }
            
            return {'passed': True, 'type': 'process_analysis'}
            
        except Exception as e:
            self.logger.error(f"Process analysis error: {e}")
            return {'passed': True, 'type': 'process_analysis_error'}
    
    def _generate_security_reason(self, risks: List[Dict[str, any]], passed: bool) -> str:
        """Generate human-readable security check reason."""
        if passed:
            return "Security checks passed"
        
        if not risks:
            return "Security check failed for unknown reasons"
        
        # Group risks by type
        risk_types = [risk['type'] for risk in risks]
        
        if 'live_game_detected' in risk_types:
            return "Live chess game detected - spectator mode only"
        elif 'rate_limit_exceeded' in risk_types:
            return "Too many analysis requests - please wait"
        elif 'rapid_analysis_requests' in risk_types:
            return "Analysis requests too frequent - anti-cheat delay required"
        elif 'suspicious_processes' in risk_types:
            return "Suspicious software detected"
        elif 'multiple_chess_windows' in risk_types:
            return "Multiple chess applications detected"
        else:
            return f"Security concerns detected: {', '.join(risk_types)}"
    
    def log_analysis_request(self, fen: str, timestamp: float) -> None:
        """Log an analysis request for monitoring."""
        analysis_entry = {
            'fen': fen,
            'timestamp': timestamp,
            'fen_hash': hashlib.md5(fen.encode()).hexdigest()
        }
        
        self.analysis_history.append(analysis_entry)
        
        # Keep only recent history (last 100 entries)
        if len(self.analysis_history) > 100:
            self.analysis_history = self.analysis_history[-100:]
    
    def get_security_status(self) -> Dict[str, any]:
        """Get current security status summary."""
        current_time = time.time()
        
        return {
            'last_check': self.last_analysis_time,
            'requests_in_window': self.request_count,
            'window_start': self.request_window_start,
            'analysis_history_count': len(self.analysis_history),
            'config': {
                'min_delay': self.config.min_analysis_delay,
                'rate_limit': self.config.rate_limit_requests,
                'spectator_only': self.config.spectator_mode_only,
                'block_live_games': self.config.block_live_games
            }
        }