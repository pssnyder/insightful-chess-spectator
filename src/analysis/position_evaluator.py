"""
Position evaluator for converting quantitative analysis into qualitative insights.
Transforms raw engine data into human-readable chess commentary.
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import chess
import logging

from .chess_engine import EngineAnalysis

@dataclass
class QualitativeEvaluation:
    """Qualitative evaluation of a chess position."""
    overall_assessment: str  # "Equal", "Slight advantage White", "Winning for Black", etc.
    game_phase: str  # "Opening", "Middlegame", "Endgame"
    key_factors: List[str]  # Main positional factors
    material_situation: str  # Material balance description
    tactical_themes: List[str]  # Tactical motifs present
    strategic_themes: List[str]  # Strategic concepts
    king_safety_status: str  # King safety assessment
    pawn_structure_notes: str  # Pawn structure evaluation
    piece_activity_notes: str  # Piece activity evaluation
    urgency_level: str  # "Low", "Medium", "High" - how critical the position is
    educational_points: List[str]  # Key learning points for viewers

class PositionEvaluator:
    """Converts engine analysis into qualitative insights."""
    
    def __init__(self):
        self.logger = logging.getLogger("chess_spectator.analysis.evaluator")
        
        # Evaluation thresholds (in centipawns)
        self.thresholds = {
            'decisive': 500,  # Winning advantage
            'significant': 200,  # Clear advantage
            'slight': 50,  # Small advantage
            'equal': 25  # Roughly equal
        }
    
    def evaluate_position(self, fen: str, analysis: EngineAnalysis) -> QualitativeEvaluation:
        """Convert engine analysis to qualitative evaluation."""
        try:
            board = chess.Board(fen)
            
            # Overall assessment
            overall = self._assess_overall_position(analysis.evaluation, analysis.mate_in)
            
            # Game phase
            game_phase = self._determine_game_phase(board, analysis.material_balance)
            
            # Key factors
            key_factors = self._identify_key_factors(board, analysis)
            
            # Material situation
            material_situation = self._describe_material_balance(analysis.material_balance)
            
            # Tactical and strategic themes
            tactical_themes = self._identify_tactical_themes(board, analysis)
            strategic_themes = self._identify_strategic_themes(board, analysis)
            
            # Specific evaluations
            king_safety = self._evaluate_king_safety(analysis.king_safety)
            pawn_structure = self._evaluate_pawn_structure(analysis.pawn_structure)
            piece_activity = self._evaluate_piece_activity(analysis.piece_activity)
            
            # Urgency and educational value
            urgency = self._determine_urgency(analysis)
            educational_points = self._generate_educational_points(board, analysis)
            
            return QualitativeEvaluation(
                overall_assessment=overall,
                game_phase=game_phase,
                key_factors=key_factors,
                material_situation=material_situation,
                tactical_themes=tactical_themes,
                strategic_themes=strategic_themes,
                king_safety_status=king_safety,
                pawn_structure_notes=pawn_structure,
                piece_activity_notes=piece_activity,
                urgency_level=urgency,
                educational_points=educational_points
            )
            
        except Exception as e:
            self.logger.error(f"Evaluation error: {e}")
            return self._create_fallback_evaluation()
    
    def _assess_overall_position(self, evaluation: float, mate_in: Optional[int]) -> str:
        """Assess the overall position."""
        if mate_in is not None:
            if mate_in > 0:
                return "Forced mate for White"
            else:
                return "Forced mate for Black"
        
        abs_eval = abs(evaluation)
        
        if abs_eval >= self.thresholds['decisive']:
            advantage = "Winning for" if abs_eval >= 800 else "Decisive advantage to"
            side = "White" if evaluation > 0 else "Black"
            return f"{advantage} {side}"
        
        elif abs_eval >= self.thresholds['significant']:
            side = "White" if evaluation > 0 else "Black"
            return f"Clear advantage to {side}"
        
        elif abs_eval >= self.thresholds['slight']:
            side = "White" if evaluation > 0 else "Black"
            return f"Slight advantage to {side}"
        
        else:
            return "Roughly equal position"
    
    def _determine_game_phase(self, board: chess.Board, material_balance: Optional[Dict[str, Any]]) -> str:
        """Determine the current game phase."""
        try:
            # Count pieces to determine phase
            piece_count = len(board.piece_map())
            
            # Queen presence
            white_queen = any(piece.piece_type == chess.QUEEN and piece.color == chess.WHITE 
                            for piece in board.piece_map().values())
            black_queen = any(piece.piece_type == chess.QUEEN and piece.color == chess.BLACK 
                            for piece in board.piece_map().values())
            
            # Simple phase determination
            if piece_count >= 28:  # Most pieces on board
                return "Opening"
            elif piece_count <= 12 or (not white_queen and not black_queen):  # Few pieces or no queens
                return "Endgame"
            else:
                return "Middlegame"
                
        except Exception:
            return "Middlegame"  # Default
    
    def _identify_key_factors(self, board: chess.Board, analysis: EngineAnalysis) -> List[str]:
        """Identify the most important positional factors."""
        factors = []
        
        try:
            # Material imbalance
            if analysis.material_balance:
                material_diff = abs(analysis.material_balance.get('difference', 0))
                if material_diff >= 3:
                    factors.append("Material imbalance")
            
            # King safety
            if analysis.king_safety:
                white_safety = analysis.king_safety.get('white_safety', 50)
                black_safety = analysis.king_safety.get('black_safety', 50)
                if abs(white_safety - black_safety) > 20:
                    factors.append("King safety")
            
            # Piece activity
            if analysis.piece_activity:
                white_activity = analysis.piece_activity.get('white_activity', 50)
                black_activity = analysis.piece_activity.get('black_activity', 50)
                if abs(white_activity - black_activity) > 15:
                    factors.append("Piece activity")
            
            # Check status
            if board.is_check():
                factors.append("King in check")
            
            # Castling rights
            if board.has_castling_rights(chess.WHITE) or board.has_castling_rights(chess.BLACK):
                factors.append("Castling rights")
            
            # Center control (simplified)
            center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
            controlled_center = 0
            for square in center_squares:
                piece = board.piece_at(square)
                if piece:
                    controlled_center += 1
            
            if controlled_center >= 2:
                factors.append("Center control")
                
        except Exception as e:
            self.logger.error(f"Error identifying key factors: {e}")
        
        return factors[:5]  # Limit to top 5 factors
    
    def _describe_material_balance(self, material_balance: Optional[Dict[str, Any]]) -> str:
        """Describe the material situation."""
        if not material_balance:
            return "Material balance unclear"
        
        try:
            difference = material_balance.get('difference', 0)
            white_total = material_balance.get('white_total', 0)
            black_total = material_balance.get('black_total', 0)
            
            if abs(difference) <= 1:
                return "Material is roughly equal"
            elif difference > 0:
                if difference >= 5:
                    return f"White has a significant material advantage ({difference} points)"
                else:
                    return f"White has a slight material advantage ({difference} points)"
            else:
                if abs(difference) >= 5:
                    return f"Black has a significant material advantage ({abs(difference)} points)"
                else:
                    return f"Black has a slight material advantage ({abs(difference)} points)"
                    
        except Exception:
            return "Material balance unclear"
    
    def _identify_tactical_themes(self, board: chess.Board, analysis: EngineAnalysis) -> List[str]:
        """Identify tactical themes in the position."""
        themes = []
        
        try:
            # Check for obvious tactical motifs
            if board.is_check():
                themes.append("Check")
            
            # Look for pieces that can be captured
            for square, piece in board.piece_map().items():
                attackers = board.attackers(not piece.color, square)
                if attackers:
                    defenders = board.attackers(piece.color, square)
                    if len(attackers) > len(defenders):
                        themes.append("Hanging pieces")
                        break
            
            # Pins and skewers (simplified detection)
            for square in chess.SQUARES:
                piece = board.piece_at(square)
                if piece and piece.piece_type in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                    # Check for potential pins/skewers along lines
                    themes.append("Pin/skewer threats")
                    break
            
            # Fork possibilities (simplified)
            for square in chess.SQUARES:
                piece = board.piece_at(square)
                if piece and piece.piece_type == chess.KNIGHT:
                    # Knight fork potential
                    knight_moves = board.attacks(square)
                    targets = 0
                    for target_square in knight_moves:
                        target_piece = board.piece_at(target_square)
                        if target_piece and target_piece.color != piece.color:
                            targets += 1
                    if targets >= 2:
                        themes.append("Fork opportunities")
                        break
                        
        except Exception as e:
            self.logger.error(f"Error identifying tactical themes: {e}")
        
        return themes[:3]  # Limit to top 3 themes
    
    def _identify_strategic_themes(self, board: chess.Board, analysis: EngineAnalysis) -> List[str]:
        """Identify strategic themes in the position."""
        themes = []
        
        try:
            # Pawn structure themes
            if analysis.pawn_structure:
                doubled = analysis.pawn_structure.get('white_doubled', 0) + analysis.pawn_structure.get('black_doubled', 0)
                isolated = analysis.pawn_structure.get('white_isolated', 0) + analysis.pawn_structure.get('black_isolated', 0)
                
                if doubled > 0:
                    themes.append("Doubled pawns")
                if isolated > 0:
                    themes.append("Isolated pawns")
            
            # Space advantage
            if analysis.piece_activity:
                white_activity = analysis.piece_activity.get('white_activity', 50)
                black_activity = analysis.piece_activity.get('black_activity', 50)
                if abs(white_activity - black_activity) > 20:
                    themes.append("Space advantage")
            
            # Development
            game_phase = self._determine_game_phase(board, analysis.material_balance)
            if game_phase == "Opening":
                themes.append("Piece development")
            
            # Weak squares (simplified detection)
            weak_square_detected = False
            for color in [chess.WHITE, chess.BLACK]:
                for square in chess.SQUARES:
                    if not board.piece_at(square):
                        # Check if square can be occupied safely
                        defenders = board.attackers(color, square)
                        attackers = board.attackers(not color, square)
                        if defenders and not attackers:
                            weak_square_detected = True
                            break
                if weak_square_detected:
                    break
            
            if weak_square_detected:
                themes.append("Weak squares")
                
        except Exception as e:
            self.logger.error(f"Error identifying strategic themes: {e}")
        
        return themes[:3]  # Limit to top 3 themes
    
    def _evaluate_king_safety(self, king_safety: Optional[Dict[str, float]]) -> str:
        """Evaluate king safety situation."""
        if not king_safety:
            return "King safety assessment unavailable"
        
        try:
            white_safety = king_safety.get('white_safety', 50)
            black_safety = king_safety.get('black_safety', 50)
            
            if white_safety > 70 and black_safety > 70:
                return "Both kings are relatively safe"
            elif white_safety < 30 and black_safety < 30:
                return "Both kings are in danger"
            elif white_safety > black_safety + 20:
                return "White king is safer than Black king"
            elif black_safety > white_safety + 20:
                return "Black king is safer than White king"
            else:
                return "King safety is roughly balanced"
                
        except Exception:
            return "King safety assessment unclear"
    
    def _evaluate_pawn_structure(self, pawn_structure: Optional[Dict[str, Any]]) -> str:
        """Evaluate pawn structure."""
        if not pawn_structure:
            return "Pawn structure assessment unavailable"
        
        try:
            white_doubled = pawn_structure.get('white_doubled', 0)
            black_doubled = pawn_structure.get('black_doubled', 0)
            white_isolated = pawn_structure.get('white_isolated', 0)
            black_isolated = pawn_structure.get('black_isolated', 0)
            
            issues = []
            
            if white_doubled > black_doubled:
                issues.append("White has doubled pawns")
            elif black_doubled > white_doubled:
                issues.append("Black has doubled pawns")
            
            if white_isolated > black_isolated:
                issues.append("White has isolated pawns")
            elif black_isolated > white_isolated:
                issues.append("Black has isolated pawns")
            
            if not issues:
                return "Pawn structure is healthy for both sides"
            else:
                return "; ".join(issues)
                
        except Exception:
            return "Pawn structure assessment unclear"
    
    def _evaluate_piece_activity(self, piece_activity: Optional[Dict[str, float]]) -> str:
        """Evaluate piece activity."""
        if not piece_activity:
            return "Piece activity assessment unavailable"
        
        try:
            white_activity = piece_activity.get('white_activity', 50)
            black_activity = piece_activity.get('black_activity', 50)
            
            if abs(white_activity - black_activity) < 10:
                return "Piece activity is roughly balanced"
            elif white_activity > black_activity:
                return "White pieces are more active"
            else:
                return "Black pieces are more active"
                
        except Exception:
            return "Piece activity assessment unclear"
    
    def _determine_urgency(self, analysis: EngineAnalysis) -> str:
        """Determine the urgency level of the position."""
        try:
            if analysis.mate_in is not None:
                return "High"  # Forced mate
            
            abs_eval = abs(analysis.evaluation)
            
            if abs_eval >= self.thresholds['decisive']:
                return "High"  # Decisive advantage
            elif abs_eval >= self.thresholds['significant']:
                return "Medium"  # Clear advantage
            else:
                return "Low"  # Equal or slight advantage
                
        except Exception:
            return "Medium"  # Default
    
    def _generate_educational_points(self, board: chess.Board, analysis: EngineAnalysis) -> List[str]:
        """Generate educational points for viewers."""
        points = []
        
        try:
            # Basic chess principles
            game_phase = self._determine_game_phase(board, analysis.material_balance)
            
            if game_phase == "Opening":
                points.append("In the opening, focus on piece development and center control")
                if not (board.has_castling_rights(chess.WHITE) or board.has_castling_rights(chess.BLACK)):
                    points.append("Both sides have lost castling rights - king safety is important")
            
            elif game_phase == "Middlegame":
                points.append("In the middlegame, look for tactical opportunities and strategic improvements")
                if analysis.piece_activity:
                    points.append("Active pieces are often more valuable than passive ones")
            
            elif game_phase == "Endgame":
                points.append("In the endgame, king activity and pawn promotion become crucial")
                if analysis.material_balance and abs(analysis.material_balance.get('difference', 0)) <= 2:
                    points.append("Small material advantages can be decisive in the endgame")
            
            # Position-specific advice
            if board.is_check():
                points.append("When in check, you must immediately address the threat to your king")
            
            if analysis.material_balance and analysis.material_balance.get('difference', 0) != 0:
                points.append("Material advantage should generally be converted into other advantages")
                
        except Exception as e:
            self.logger.error(f"Error generating educational points: {e}")
        
        return points[:3]  # Limit to top 3 points
    
    def _create_fallback_evaluation(self) -> QualitativeEvaluation:
        """Create a fallback evaluation when analysis fails."""
        return QualitativeEvaluation(
            overall_assessment="Position assessment unavailable",
            game_phase="Unknown",
            key_factors=["Analysis temporarily unavailable"],
            material_situation="Material balance unclear",
            tactical_themes=[],
            strategic_themes=[],
            king_safety_status="King safety assessment unavailable",
            pawn_structure_notes="Pawn structure assessment unavailable",
            piece_activity_notes="Piece activity assessment unavailable",
            urgency_level="Medium",
            educational_points=["Analysis will resume shortly"]
        )