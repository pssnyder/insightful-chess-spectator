"""
Chess board detection and piece recognition using computer vision.
Identifies chess board positions and converts them to FEN notation.
"""

import asyncio
import time
from typing import Optional, List, Tuple, Dict
import numpy as np
import cv2
import chess
from dataclasses import dataclass
import logging

from ..config.settings import VisionConfig

@dataclass
class BoardInfo:
    """Information about a detected chess board."""
    fen: str
    board_corners: Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int], Tuple[int, int]]
    square_size: int
    is_flipped: bool = False
    confidence: float = 0.0
    detection_time: float = 0.0

@dataclass
class PieceInfo:
    """Information about a detected chess piece."""
    piece_type: str  # 'p', 'r', 'n', 'b', 'q', 'k'
    color: str       # 'w' or 'b'
    square: str      # e.g., 'e4'
    confidence: float
    position: Tuple[int, int]  # pixel coordinates

class BoardDetector:
    """Detects chess boards and pieces in images."""
    
    def __init__(self, config: VisionConfig):
        self.config = config
        self.logger = logging.getLogger("chess_spectator.vision.detector")
        
        # Board detection parameters
        self.min_square_size = config.square_size_min
        self.max_square_size = config.square_size_max
        
        # Color templates for piece detection
        self.piece_templates = {}
        self.color_ranges = {
            'light_squares': {'lower': np.array([200, 200, 180]), 'upper': np.array([255, 255, 255])},
            'dark_squares': {'lower': np.array([80, 60, 40]), 'upper': np.array([140, 120, 100])},
            'white_pieces': {'lower': np.array([200, 200, 200]), 'upper': np.array([255, 255, 255])},
            'black_pieces': {'lower': np.array([0, 0, 0]), 'upper': np.array([80, 80, 80])}
        }
        
        self._load_piece_templates()
    
    def _load_piece_templates(self):
        """Load piece recognition templates."""
        # For now, we'll use basic shape detection
        # In a full implementation, you'd load actual piece images
        self.logger.info("Piece templates loaded (using basic shape detection)")
    
    async def detect_board(self, image: np.ndarray) -> Optional[BoardInfo]:
        """Detect a chess board in the given image."""
        start_time = time.time()
        
        try:
            # Find board boundaries
            board_corners = await self._find_board_boundaries(image)
            if board_corners is None:
                return None
            
            # Extract board region
            board_image = self._extract_board_region(image, board_corners)
            if board_image is None:
                return None
            
            # Detect pieces
            pieces = await self._detect_pieces(board_image)
            
            # Convert to FEN
            fen = self._pieces_to_fen(pieces)
            
            # Calculate square size
            square_size = self._calculate_square_size(board_corners)
            
            detection_time = time.time() - start_time
            
            board_info = BoardInfo(
                fen=fen,
                board_corners=board_corners,
                square_size=square_size,
                confidence=0.8,  # Placeholder - implement proper confidence calculation
                detection_time=detection_time
            )
            
            self.logger.debug(f"Board detected in {detection_time:.3f}s: {fen}")
            return board_info
            
        except Exception as e:
            self.logger.error(f"Board detection error: {e}")
            return None
    
    async def _find_board_boundaries(self, image: np.ndarray) -> Optional[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int], Tuple[int, int]]]:
        """Find the boundaries of the chess board."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Look for rectangular contours that could be chess boards
            for contour in contours:
                # Approximate contour to polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Check if it's a quadrilateral
                if len(approx) == 4:
                    # Check if it's roughly square and large enough
                    area = cv2.contourArea(approx)
                    if area > (self.min_square_size * 8) ** 2:
                        # Extract corners
                        corners = tuple(tuple(point[0]) for point in approx)
                        return corners
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding board boundaries: {e}")
            return None
    
    def _extract_board_region(self, image: np.ndarray, corners: Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int], Tuple[int, int]]) -> Optional[np.ndarray]:
        """Extract the board region from the image."""
        try:
            # Convert corners to numpy array
            src_points = np.array(corners, dtype=np.float32)
            
            # Define destination points (square board)
            board_size = 640  # Standard size for processing
            dst_points = np.array([
                [0, 0],
                [board_size, 0],
                [board_size, board_size],
                [0, board_size]
            ], dtype=np.float32)
            
            # Calculate perspective transformation
            matrix = cv2.getPerspectiveTransform(src_points, dst_points)
            
            # Apply transformation
            board_image = cv2.warpPerspective(image, matrix, (board_size, board_size))
            
            return board_image
            
        except Exception as e:
            self.logger.error(f"Error extracting board region: {e}")
            return None
    
    async def _detect_pieces(self, board_image: np.ndarray) -> List[PieceInfo]:
        """Detect pieces on the chess board."""
        pieces = []
        
        try:
            # Divide board into 8x8 squares
            height, width = board_image.shape[:2]
            square_height = height // 8
            square_width = width // 8
            
            for row in range(8):
                for col in range(8):
                    # Extract square
                    y1 = row * square_height
                    y2 = (row + 1) * square_height
                    x1 = col * square_width
                    x2 = (col + 1) * square_width
                    
                    square_image = board_image[y1:y2, x1:x2]
                    
                    # Detect piece in square
                    piece_info = await self._analyze_square(square_image, row, col)
                    if piece_info:
                        pieces.append(piece_info)
            
        except Exception as e:
            self.logger.error(f"Error detecting pieces: {e}")
        
        return pieces
    
    async def _analyze_square(self, square_image: np.ndarray, row: int, col: int) -> Optional[PieceInfo]:
        """Analyze a single square for piece presence and type."""
        try:
            # Convert square coordinates to chess notation
            file_letter = chr(ord('a') + col)
            rank_number = str(8 - row)
            square_name = file_letter + rank_number
            
            # Basic piece detection using color analysis
            # This is a simplified approach - real implementation would use template matching
            
            # Calculate average color
            avg_color = np.mean(square_image, axis=(0, 1))
            
            # Check if square has a piece (different from background)
            # This is a placeholder - implement proper piece detection
            gray_square = cv2.cvtColor(square_image, cv2.COLOR_BGR2GRAY)
            
            # Simple edge-based piece detection
            edges = cv2.Canny(gray_square, 30, 100)
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            
            if edge_density > 0.05:  # Threshold for piece presence
                # Determine piece color based on brightness
                brightness = np.mean(gray_square)
                piece_color = 'w' if brightness > 128 else 'b'
                
                # For now, just detect pawns (would need more sophisticated detection)
                piece_type = 'p'  # Placeholder
                
                return PieceInfo(
                    piece_type=piece_type,
                    color=piece_color,
                    square=square_name,
                    confidence=0.7,  # Placeholder
                    position=(col * 80 + 40, row * 80 + 40)  # Center of square
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing square {row},{col}: {e}")
            return None
    
    def _pieces_to_fen(self, pieces: List[PieceInfo]) -> str:
        """Convert detected pieces to FEN notation."""
        try:
            # Initialize empty board
            board = chess.Board(fen=None)
            board.clear()
            
            # Place detected pieces
            for piece_info in pieces:
                square = chess.parse_square(piece_info.square)
                piece_symbol = piece_info.piece_type
                if piece_info.color == 'w':
                    piece_symbol = piece_symbol.upper()
                
                piece = chess.Piece.from_symbol(piece_symbol)
                board.set_piece_at(square, piece)
            
            return board.fen()
            
        except Exception as e:
            self.logger.error(f"Error converting pieces to FEN: {e}")
            # Return starting position as fallback
            return chess.STARTING_FEN
    
    def _calculate_square_size(self, corners: Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int], Tuple[int, int]]) -> int:
        """Calculate the size of a chess square in pixels."""
        try:
            # Calculate average distance between corners
            distances = []
            for i in range(4):
                x1, y1 = corners[i]
                x2, y2 = corners[(i + 1) % 4]
                distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                distances.append(distance)
            
            avg_side_length = sum(distances) / len(distances)
            square_size = int(avg_side_length / 8)  # Divide by 8 squares
            
            return max(self.min_square_size, min(square_size, self.max_square_size))
            
        except Exception as e:
            self.logger.error(f"Error calculating square size: {e}")
            return 60  # Default square size