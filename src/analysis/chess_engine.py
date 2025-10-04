"""
Chess engine integration using Stockfish for position analysis.
Provides move evaluation, best lines, and position assessment.
"""

import asyncio
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import chess
import chess.engine
from stockfish import Stockfish
import logging

from ..config.settings import AnalysisConfig

@dataclass
class EngineAnalysis:
    """Results from chess engine analysis."""
    fen: str
    evaluation: float  # In centipawns
    best_move: Optional[str]
    principal_variation: List[str]
    depth: int
    time_taken: float
    nodes_searched: int
    mate_in: Optional[int] = None
    
    # Additional analysis data
    material_balance: Optional[Dict[str, Any]] = None
    piece_activity: Optional[Dict[str, float]] = None
    king_safety: Optional[Dict[str, float]] = None
    pawn_structure: Optional[Dict[str, Any]] = None

class ChessAnalyzer:
    """Chess position analyzer using Stockfish engine."""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.logger = logging.getLogger("chess_spectator.analysis.engine")
        
        # Stockfish engine instance
        self.engine: Optional[Stockfish] = None
        self.engine_path = self._find_stockfish_path()
        
        self._initialize_engine()
    
    def _find_stockfish_path(self) -> str:
        """Find Stockfish executable path."""
        # Common Stockfish installation paths
        possible_paths = [
            "stockfish",  # If in PATH
            "engines/stockfish",
            "stockfish/stockfish.exe",
            "/usr/local/bin/stockfish",
            "/usr/bin/stockfish",
            "C:/stockfish/stockfish.exe",
        ]
        
        for path in possible_paths:
            try:
                # Test if Stockfish is available at this path
                test_engine = Stockfish(path=path)
                test_engine.set_position([])  # Test basic functionality
                self.logger.info(f"Found Stockfish at: {path}")
                return path
            except Exception:
                continue
        
        # Default fallback
        self.logger.warning("Stockfish not found in common locations, using default path")
        return "stockfish"
    
    def _initialize_engine(self):
        """Initialize the Stockfish engine with configuration."""
        try:
            self.engine = Stockfish(
                path=self.engine_path,
                parameters={
                    "Threads": 4,
                    "Hash": 256,
                    "Ponder": False,
                    "MultiPV": self.config.max_variations,
                    "UCI_AnalyseMode": True,
                    "UCI_LimitStrength": False
                }
            )
            
            if self.engine.is_valid():
                self.logger.info("Stockfish engine initialized successfully")
            else:
                raise Exception("Stockfish engine validation failed")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Stockfish: {e}")
            self.engine = None
    
    async def analyze_position(self, fen: str) -> Optional[EngineAnalysis]:
        """Analyze a chess position and return detailed evaluation."""
        if not self.engine or not self.engine.is_valid():
            self.logger.error("Stockfish engine not available")
            return None
        
        start_time = time.time()
        
        try:
            # Set the position
            board = chess.Board(fen)
            moves = []
            
            # Convert position to move list for Stockfish
            temp_board = chess.Board()
            for move in board.move_stack:
                moves.append(move.uci())
            
            self.engine.set_position(moves)
            
            # Get evaluation
            evaluation = self.engine.get_evaluation()
            
            # Get best move
            best_move = self.engine.get_best_move_time(int(self.config.stockfish_time * 1000))
            
            # Get principal variation
            pv = []
            if best_move:
                pv.append(best_move)
                # For now, just get the best move. In full implementation,
                # you'd get the full principal variation
            
            # Parse evaluation
            eval_score = 0.0
            mate_in = None
            
            if evaluation['type'] == 'cp':
                eval_score = evaluation['value']
            elif evaluation['type'] == 'mate':
                mate_in = evaluation['value']
                eval_score = 9999 if mate_in > 0 else -9999
            
            # Additional analysis
            material_balance = self._calculate_material_balance(board)
            piece_activity = await self._analyze_piece_activity(board)
            king_safety = await self._analyze_king_safety(board)
            pawn_structure = await self._analyze_pawn_structure(board)
            
            analysis_time = time.time() - start_time
            
            return EngineAnalysis(
                fen=fen,
                evaluation=eval_score,
                best_move=best_move,
                principal_variation=pv,
                depth=self.config.stockfish_depth,
                time_taken=analysis_time,
                nodes_searched=0,  # Stockfish wrapper doesn't provide this easily
                mate_in=mate_in,
                material_balance=material_balance,
                piece_activity=piece_activity,
                king_safety=king_safety,
                pawn_structure=pawn_structure
            )
            
        except Exception as e:
            self.logger.error(f"Analysis error: {e}")
            return None
    
    def _calculate_material_balance(self, board: chess.Board) -> Dict[str, int]:
        """Calculate material balance for both sides."""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        
        white_material = 0
        black_material = 0
        white_pieces = {}
        black_pieces = {}
        
        for square, piece in board.piece_map().items():
            value = piece_values[piece.piece_type]
            
            if piece.color == chess.WHITE:
                white_material += value
                piece_name = chess.piece_name(piece.piece_type)
                white_pieces[piece_name] = white_pieces.get(piece_name, 0) + 1
            else:
                black_material += value
                piece_name = chess.piece_name(piece.piece_type)
                black_pieces[piece_name] = black_pieces.get(piece_name, 0) + 1
        
        return {
            'white_total': white_material,
            'black_total': black_material,
            'difference': white_material - black_material,
            'white_pieces': white_pieces,
            'black_pieces': black_pieces
        }
    
    async def _analyze_piece_activity(self, board: chess.Board) -> Dict[str, float]:
        """Analyze piece activity and mobility."""
        try:
            white_mobility = 0
            black_mobility = 0
            
            # Count legal moves for each side
            if board.turn == chess.WHITE:
                white_mobility = len(list(board.legal_moves))
                # Switch turn to count black moves
                board.push(chess.Move.null())
                black_mobility = len(list(board.legal_moves))
                board.pop()
            else:
                black_mobility = len(list(board.legal_moves))
                # Switch turn to count white moves
                board.push(chess.Move.null())
                white_mobility = len(list(board.legal_moves))
                board.pop()
            
            total_mobility = white_mobility + black_mobility
            
            return {
                'white_mobility': white_mobility,
                'black_mobility': black_mobility,
                'white_activity': white_mobility / max(total_mobility, 1) * 100,
                'black_activity': black_mobility / max(total_mobility, 1) * 100
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing piece activity: {e}")
            return {'white_activity': 50.0, 'black_activity': 50.0}
    
    async def _analyze_king_safety(self, board: chess.Board) -> Dict[str, float]:
        """Analyze king safety for both sides."""
        try:
            white_king_square = board.king(chess.WHITE)
            black_king_square = board.king(chess.BLACK)
            
            # Simple king safety evaluation
            white_safety = 50.0
            black_safety = 50.0
            
            if white_king_square:
                # Check if white king is castled
                if white_king_square in [chess.G1, chess.C1]:
                    white_safety += 20.0
                
                # Check for pawn shelter
                king_file = chess.square_file(white_king_square)
                for file_offset in [-1, 0, 1]:
                    check_file = king_file + file_offset
                    if 0 <= check_file <= 7:
                        pawn_square = chess.square(check_file, 1)  # Rank 2
                        if board.piece_at(pawn_square) and board.piece_at(pawn_square).piece_type == chess.PAWN:
                            white_safety += 5.0
            
            if black_king_square:
                # Check if black king is castled
                if black_king_square in [chess.G8, chess.C8]:
                    black_safety += 20.0
                
                # Check for pawn shelter
                king_file = chess.square_file(black_king_square)
                for file_offset in [-1, 0, 1]:
                    check_file = king_file + file_offset
                    if 0 <= check_file <= 7:
                        pawn_square = chess.square(check_file, 6)  # Rank 7
                        if board.piece_at(pawn_square) and board.piece_at(pawn_square).piece_type == chess.PAWN:
                            black_safety += 5.0
            
            return {
                'white_safety': min(white_safety, 100.0),
                'black_safety': min(black_safety, 100.0)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing king safety: {e}")
            return {'white_safety': 50.0, 'black_safety': 50.0}
    
    async def _analyze_pawn_structure(self, board: chess.Board) -> Dict[str, Any]:
        """Analyze pawn structure characteristics."""
        try:
            white_pawns = []
            black_pawns = []
            
            # Find all pawns
            for square, piece in board.piece_map().items():
                if piece.piece_type == chess.PAWN:
                    if piece.color == chess.WHITE:
                        white_pawns.append(square)
                    else:
                        black_pawns.append(square)
            
            # Analyze pawn structure
            white_doubled = self._count_doubled_pawns(white_pawns)
            black_doubled = self._count_doubled_pawns(black_pawns)
            
            white_isolated = self._count_isolated_pawns(white_pawns)
            black_isolated = self._count_isolated_pawns(black_pawns)
            
            return {
                'white_pawn_count': len(white_pawns),
                'black_pawn_count': len(black_pawns),
                'white_doubled': white_doubled,
                'black_doubled': black_doubled,
                'white_isolated': white_isolated,
                'black_isolated': black_isolated
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing pawn structure: {e}")
            return {
                'white_pawn_count': 8,
                'black_pawn_count': 8,
                'white_doubled': 0,
                'black_doubled': 0,
                'white_isolated': 0,
                'black_isolated': 0
            }
    
    def _count_doubled_pawns(self, pawn_squares: List[int]) -> int:
        """Count doubled pawns."""
        files = {}
        for square in pawn_squares:
            file_idx = chess.square_file(square)
            files[file_idx] = files.get(file_idx, 0) + 1
        
        doubled_count = 0
        for count in files.values():
            if count > 1:
                doubled_count += count - 1
        
        return doubled_count
    
    def _count_isolated_pawns(self, pawn_squares: List[int]) -> int:
        """Count isolated pawns."""
        if not pawn_squares:
            return 0
        
        files_with_pawns = set(chess.square_file(square) for square in pawn_squares)
        isolated_count = 0
        
        for file_idx in files_with_pawns:
            has_neighbor = False
            for neighbor_file in [file_idx - 1, file_idx + 1]:
                if neighbor_file in files_with_pawns:
                    has_neighbor = True
                    break
            
            if not has_neighbor:
                isolated_count += 1
        
        return isolated_count
    
    async def cleanup(self):
        """Cleanup engine resources."""
        try:
            if self.engine:
                # Stockfish wrapper handles cleanup automatically
                self.engine = None
                self.logger.info("Chess engine cleanup complete")
        except Exception as e:
            self.logger.error(f"Error during engine cleanup: {e}")