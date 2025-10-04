"""
AI-powered commentary generation using Firebase AI services.
Converts chess analysis into natural language commentary for viewers.
"""

import asyncio
import time
from typing import Optional, List, Dict, Any
import json
import logging
from dataclasses import dataclass

# Firebase imports
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    import google.generativeai as genai
except ImportError:
    firebase_admin = None
    firestore = None
    genai = None

from ..config.settings import FirebaseConfig
from ..analysis.chess_engine import EngineAnalysis
from ..analysis.position_evaluator import QualitativeEvaluation

@dataclass
class CommentaryStyle:
    """Commentary style configuration."""
    name: str
    tone: str  # "casual", "formal", "educational", "entertaining"
    detail_level: str  # "basic", "intermediate", "advanced"
    target_audience: str  # "beginners", "club_players", "advanced"
    max_length: int = 500

class CommentaryGenerator:
    """Generates natural language commentary for chess positions."""
    
    def __init__(self, config: FirebaseConfig):
        self.config = config
        self.logger = logging.getLogger("chess_spectator.ai.commentary")
        
        # Commentary styles
        self.styles = {
            "educational": CommentaryStyle(
                name="Educational",
                tone="educational",
                detail_level="intermediate",
                target_audience="club_players",
                max_length=400
            ),
            "casual": CommentaryStyle(
                name="Casual",
                tone="casual",
                detail_level="basic",
                target_audience="beginners",
                max_length=300
            ),
            "formal": CommentaryStyle(
                name="Formal",
                tone="formal",
                detail_level="advanced",
                target_audience="advanced",
                max_length=500
            ),
            "entertaining": CommentaryStyle(
                name="Entertaining",
                tone="entertaining",
                detail_level="intermediate",
                target_audience="club_players",
                max_length=350
            )
        }
        
        self.current_style = self.styles["educational"]
        
        # Firebase and AI initialization
        self.firebase_app = None
        self.firestore_client = None
        self.ai_model = None
        
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize Firebase and AI services."""
        try:
            if not firebase_admin or not self.config.project_id:
                self.logger.warning("Firebase not available or not configured")
                return
            
            # Initialize Firebase if not already done
            if not firebase_admin._apps:
                if self.config.credentials_path:
                    cred = credentials.Certificate(self.config.credentials_path)
                    self.firebase_app = firebase_admin.initialize_app(cred)
                else:
                    # Use default credentials
                    self.firebase_app = firebase_admin.initialize_app()
                
                self.firestore_client = firestore.client()
                self.logger.info("Firebase initialized successfully")
            
            # Initialize Gemini AI (example - adjust based on your Firebase AI setup)
            if genai:
                # Configure with your API key
                # genai.configure(api_key="your-api-key")
                # self.ai_model = genai.GenerativeModel('gemini-pro')
                self.logger.info("AI model initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI services: {e}")
    
    async def generate_commentary(
        self, 
        fen: str, 
        analysis: EngineAnalysis, 
        evaluation: QualitativeEvaluation,
        style: Optional[str] = None
    ) -> str:
        """Generate commentary for a chess position."""
        
        if style and style in self.styles:
            commentary_style = self.styles[style]
        else:
            commentary_style = self.current_style
        
        try:
            # Try AI generation first, fall back to template-based
            if self.ai_model:
                commentary = await self._generate_ai_commentary(
                    fen, analysis, evaluation, commentary_style
                )
                if commentary:
                    return commentary
            
            # Fallback to template-based commentary
            return self._generate_template_commentary(
                fen, analysis, evaluation, commentary_style
            )
            
        except Exception as e:
            self.logger.error(f"Commentary generation error: {e}")
            return self._generate_fallback_commentary(evaluation)
    
    async def _generate_ai_commentary(
        self, 
        fen: str, 
        analysis: EngineAnalysis, 
        evaluation: QualitativeEvaluation,
        style: CommentaryStyle
    ) -> Optional[str]:
        """Generate commentary using AI services."""
        try:
            if not self.ai_model:
                return None
            
            # Prepare prompt for AI
            prompt = self._create_ai_prompt(fen, analysis, evaluation, style)
            
            # Generate response (example for Gemini)
            # response = await self.ai_model.generate_content_async(prompt)
            # commentary = response.text
            
            # For now, return None to use template-based generation
            # In real implementation, you'd call your AI service here
            return None
            
        except Exception as e:
            self.logger.error(f"AI commentary generation error: {e}")
            return None
    
    def _create_ai_prompt(
        self, 
        fen: str, 
        analysis: EngineAnalysis, 
        evaluation: QualitativeEvaluation,
        style: CommentaryStyle
    ) -> str:
        """Create a prompt for AI commentary generation."""
        
        prompt = f"""
        You are an expert chess commentator providing analysis for viewers. 
        
        Style: {style.tone} tone, {style.detail_level} detail level, for {style.target_audience}
        Maximum length: {style.max_length} characters
        
        Position Information:
        - Game Phase: {evaluation.game_phase}
        - Overall Assessment: {evaluation.overall_assessment}
        - Key Factors: {', '.join(evaluation.key_factors)}
        - Material: {evaluation.material_situation}
        - King Safety: {evaluation.king_safety_status}
        
        IMPORTANT RULES:
        1. Never suggest specific moves or give tactical solutions
        2. Focus on general position assessment and educational insights
        3. Use qualitative descriptions, not exact numerical evaluations
        4. Keep commentary appropriate for spectators, not players
        5. Emphasize learning opportunities and chess principles
        
        Generate commentary that explains the current position's characteristics and what viewers should notice:
        """
        
        return prompt
    
    def _generate_template_commentary(
        self, 
        fen: str, 
        analysis: EngineAnalysis, 
        evaluation: QualitativeEvaluation,
        style: CommentaryStyle
    ) -> str:
        """Generate commentary using templates."""
        
        commentary_parts = []
        
        try:
            # Opening statement based on overall assessment
            commentary_parts.append(self._get_opening_statement(evaluation, style))
            
            # Game phase context
            if evaluation.game_phase:
                phase_comment = self._get_phase_comment(evaluation.game_phase, style)
                if phase_comment:
                    commentary_parts.append(phase_comment)
            
            # Key factors
            if evaluation.key_factors:
                factors_comment = self._get_factors_comment(evaluation.key_factors, style)
                if factors_comment:
                    commentary_parts.append(factors_comment)
            
            # Material situation
            if evaluation.material_situation and "unclear" not in evaluation.material_situation.lower():
                commentary_parts.append(evaluation.material_situation)
            
            # Educational insights
            if evaluation.educational_points and style.tone == "educational":
                edu_comment = self._get_educational_comment(evaluation.educational_points)
                if edu_comment:
                    commentary_parts.append(edu_comment)
            
            # Combine parts
            full_commentary = ". ".join(commentary_parts)
            
            # Ensure proper ending
            if not full_commentary.endswith('.'):
                full_commentary += '.'
            
            # Limit length
            if len(full_commentary) > style.max_length:
                full_commentary = full_commentary[:style.max_length - 3] + "..."
            
            return full_commentary
            
        except Exception as e:
            self.logger.error(f"Template commentary error: {e}")
            return self._generate_fallback_commentary(evaluation)
    
    def _get_opening_statement(self, evaluation: QualitativeEvaluation, style: CommentaryStyle) -> str:
        """Get opening statement based on position assessment."""
        
        if style.tone == "casual":
            openings = {
                "Roughly equal": "This position looks pretty balanced",
                "Slight advantage": "One side seems to have a small edge here",
                "Clear advantage": "There's a noticeable advantage in this position",
                "Decisive advantage": "This position shows a significant imbalance",
                "Winning": "This looks like a winning position",
                "Forced mate": "There's a forced mate in this position"
            }
        elif style.tone == "formal":
            openings = {
                "Roughly equal": "The position demonstrates approximate equality",
                "Slight advantage": "The position exhibits a marginal advantage",
                "Clear advantage": "The position reveals a substantial advantage",
                "Decisive advantage": "The position shows a decisive advantage",
                "Winning": "The position is winning",
                "Forced mate": "The position contains a forced mate sequence"
            }
        else:  # educational/entertaining
            openings = {
                "Roughly equal": "This position shows the dynamic balance typical in chess",
                "Slight advantage": "We can see some positional factors favoring one side",
                "Clear advantage": "Several factors are working together to create an advantage",
                "Decisive advantage": "The position demonstrates how small advantages can accumulate",
                "Winning": "This position illustrates a winning advantage",
                "Forced mate": "This position contains tactical motifs leading to mate"
            }
        
        # Find best match
        assessment = evaluation.overall_assessment.lower()
        for key, value in openings.items():
            if key.lower() in assessment:
                return value
        
        return "This is an interesting position to analyze"
    
    def _get_phase_comment(self, game_phase: str, style: CommentaryStyle) -> Optional[str]:
        """Get comment about game phase."""
        
        phase_comments = {
            "Opening": {
                "casual": "We're still in the opening stage",
                "formal": "The position remains in the opening phase",
                "educational": "In this opening phase, development and center control are key priorities",
                "entertaining": "The opening battle is still unfolding"
            },
            "Middlegame": {
                "casual": "We've reached the middlegame",
                "formal": "The position has transitioned to the middlegame",
                "educational": "The middlegame brings opportunities for tactical and strategic play",
                "entertaining": "The real chess battle begins in this middlegame"
            },
            "Endgame": {
                "casual": "We're in the endgame now",
                "formal": "The position has entered the endgame phase",
                "educational": "Endgame technique and king activity become crucial here",
                "entertaining": "The endgame demands precision and technique"
            }
        }
        
        return phase_comments.get(game_phase, {}).get(style.tone)
    
    def _get_factors_comment(self, key_factors: List[str], style: CommentaryStyle) -> Optional[str]:
        """Get comment about key positional factors."""
        
        if not key_factors:
            return None
        
        if len(key_factors) == 1:
            factor_text = key_factors[0]
        elif len(key_factors) == 2:
            factor_text = f"{key_factors[0]} and {key_factors[1]}"
        else:
            factor_text = f"{', '.join(key_factors[:-1])}, and {key_factors[-1]}"
        
        if style.tone == "casual":
            return f"The main things to notice are {factor_text.lower()}"
        elif style.tone == "formal":
            return f"The primary positional factors include {factor_text.lower()}"
        else:
            return f"Key factors in this position include {factor_text.lower()}"
    
    def _get_educational_comment(self, educational_points: List[str]) -> Optional[str]:
        """Get educational commentary."""
        if not educational_points:
            return None
        
        # Use the first educational point
        point = educational_points[0]
        return f"From a learning perspective: {point.lower()}"
    
    def _generate_fallback_commentary(self, evaluation: QualitativeEvaluation) -> str:
        """Generate simple fallback commentary."""
        try:
            base = f"This {evaluation.game_phase.lower()} position shows {evaluation.overall_assessment.lower()}"
            
            if evaluation.key_factors:
                base += f", with {evaluation.key_factors[0].lower()} being a key factor"
            
            return base + "."
            
        except Exception:
            return "This is an interesting chess position worth analyzing."
    
    def set_commentary_style(self, style_name: str) -> bool:
        """Set the commentary style."""
        if style_name in self.styles:
            self.current_style = self.styles[style_name]
            self.logger.info(f"Commentary style set to: {style_name}")
            return True
        else:
            self.logger.warning(f"Unknown commentary style: {style_name}")
            return False
    
    def get_available_styles(self) -> List[str]:
        """Get list of available commentary styles."""
        return list(self.styles.keys())
    
    async def store_commentary(self, fen: str, commentary: str, analysis_data: Dict[str, Any]) -> None:
        """Store commentary in Firebase for analysis and improvement."""
        try:
            if not self.firestore_client:
                return
            
            doc_data = {
                'fen': fen,
                'commentary': commentary,
                'timestamp': time.time(),
                'style': self.current_style.name,
                'analysis_data': analysis_data
            }
            
            await self.firestore_client.collection(self.config.collection_name).add(doc_data)
            
        except Exception as e:
            self.logger.error(f"Error storing commentary: {e}")
    
    async def cleanup(self):
        """Cleanup AI service resources."""
        try:
            # Cleanup Firebase connections if needed
            self.logger.info("AI services cleanup complete")
        except Exception as e:
            self.logger.error(f"Error during AI cleanup: {e}")