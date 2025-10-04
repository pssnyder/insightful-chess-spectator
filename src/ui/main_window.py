"""
Main UI window for the Chess Spectator application.
Provides user interface for controlling analysis and viewing results.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import asyncio
from typing import Optional, Callable, Dict, Any
import logging
from dataclasses import dataclass

try:
    import customtkinter as ctk
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    CUSTOM_TK_AVAILABLE = True
except ImportError:
    CUSTOM_TK_AVAILABLE = False

from ..config.settings import UIConfig
from ..analysis.position_evaluator import QualitativeEvaluation

@dataclass
class UICallbacks:
    """Callbacks for UI events."""
    on_start: Optional[Callable] = None
    on_stop: Optional[Callable] = None
    on_settings: Optional[Callable] = None

class SpectatorUI:
    """Main user interface for the Chess Spectator."""
    
    def __init__(
        self, 
        config: UIConfig,
        on_start_callback: Optional[Callable] = None,
        on_stop_callback: Optional[Callable] = None,
        on_settings_callback: Optional[Callable] = None
    ):
        self.config = config
        self.logger = logging.getLogger("chess_spectator.ui.main")
        
        # Callbacks
        self.callbacks = UICallbacks(
            on_start=on_start_callback,
            on_stop=on_stop_callback,
            on_settings=on_settings_callback
        )
        
        # UI state
        self.is_analyzing = False
        self.current_fen = ""
        self.current_evaluation: Optional[QualitativeEvaluation] = None
        
        # Create main window
        self._create_main_window()
        self._create_widgets()
        self._setup_layout()
        
    def _create_main_window(self):
        """Create the main application window."""
        if CUSTOM_TK_AVAILABLE:
            self.root = ctk.CTk()
            self.root.title("Insightful Chess Spectator")
            self.root.geometry(f"{self.config.window_width}x{self.config.window_height}")
        else:
            self.root = tk.Tk()
            self.root.title("Insightful Chess Spectator")
            self.root.geometry(f"{self.config.window_width}x{self.config.window_height}")
            
        # Configure window
        self.root.minsize(800, 600)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Configure grid weights
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
    
    def _create_widgets(self):
        """Create all UI widgets."""
        
        # Control frame
        if CUSTOM_TK_AVAILABLE:
            self.control_frame = ctk.CTkFrame(self.root)
            self.start_button = ctk.CTkButton(
                self.control_frame, 
                text="Start Analysis",
                command=self._on_start_clicked
            )
            self.stop_button = ctk.CTkButton(
                self.control_frame,
                text="Stop Analysis", 
                command=self._on_stop_clicked,
                state="disabled"
            )
            self.settings_button = ctk.CTkButton(
                self.control_frame,
                text="Settings",
                command=self._on_settings_clicked
            )
        else:
            self.control_frame = ttk.Frame(self.root)
            self.start_button = ttk.Button(
                self.control_frame,
                text="Start Analysis",
                command=self._on_start_clicked
            )
            self.stop_button = ttk.Button(
                self.control_frame,
                text="Stop Analysis",
                command=self._on_stop_clicked,
                state="disabled"
            )
            self.settings_button = ttk.Button(
                self.control_frame,
                text="Settings",
                command=self._on_settings_clicked
            )
        
        # Status frame
        if CUSTOM_TK_AVAILABLE:
            self.status_frame = ctk.CTkFrame(self.root)
            self.status_label = ctk.CTkLabel(
                self.status_frame,
                text="Status: Ready"
            )
        else:
            self.status_frame = ttk.Frame(self.root)
            self.status_label = ttk.Label(
                self.status_frame,
                text="Status: Ready"
            )
        
        # Main content frame
        if CUSTOM_TK_AVAILABLE:
            self.content_frame = ctk.CTkFrame(self.root)
        else:
            self.content_frame = ttk.Frame(self.root)
        
        # Commentary display
        if CUSTOM_TK_AVAILABLE:
            self.commentary_frame = ctk.CTkFrame(self.content_frame)
            self.commentary_label = ctk.CTkLabel(
                self.commentary_frame,
                text="Commentary",
                font=("Arial", 14, "bold")
            )
            self.commentary_text = ctk.CTkTextbox(
                self.commentary_frame,
                height=150,
                wrap="word"
            )
        else:
            self.commentary_frame = ttk.LabelFrame(self.content_frame, text="Commentary")
            self.commentary_text = scrolledtext.ScrolledText(
                self.commentary_frame,
                height=8,
                wrap=tk.WORD,
                state=tk.DISABLED
            )
        
        # Analysis details frame
        if CUSTOM_TK_AVAILABLE:
            self.details_frame = ctk.CTkFrame(self.content_frame)
            self.details_label = ctk.CTkLabel(
                self.details_frame,
                text="Analysis Details",
                font=("Arial", 14, "bold")
            )
        else:
            self.details_frame = ttk.LabelFrame(self.content_frame, text="Analysis Details")
        
        # Create detail labels
        self._create_detail_labels()
        
        # Log frame
        if CUSTOM_TK_AVAILABLE:
            self.log_frame = ctk.CTkFrame(self.content_frame)
            self.log_label = ctk.CTkLabel(
                self.log_frame,
                text="Activity Log",
                font=("Arial", 12, "bold")
            )
            self.log_text = ctk.CTkTextbox(
                self.log_frame,
                height=100
            )
        else:
            self.log_frame = ttk.LabelFrame(self.content_frame, text="Activity Log")
            self.log_text = scrolledtext.ScrolledText(
                self.log_frame,
                height=5,
                wrap=tk.WORD,
                state=tk.DISABLED
            )
    
    def _create_detail_labels(self):
        """Create labels for analysis details."""
        if CUSTOM_TK_AVAILABLE:
            self.game_phase_label = ctk.CTkLabel(self.details_frame, text="Game Phase: Unknown")
            self.assessment_label = ctk.CTkLabel(self.details_frame, text="Assessment: None")
            self.material_label = ctk.CTkLabel(self.details_frame, text="Material: Balanced")
            self.king_safety_label = ctk.CTkLabel(self.details_frame, text="King Safety: Unknown")
            self.key_factors_label = ctk.CTkLabel(self.details_frame, text="Key Factors: None")
        else:
            self.game_phase_label = ttk.Label(self.details_frame, text="Game Phase: Unknown")
            self.assessment_label = ttk.Label(self.details_frame, text="Assessment: None")
            self.material_label = ttk.Label(self.details_frame, text="Material: Balanced")
            self.king_safety_label = ttk.Label(self.details_frame, text="King Safety: Unknown")
            self.key_factors_label = ttk.Label(self.details_frame, text="Key Factors: None")
    
    def _setup_layout(self):
        """Setup the widget layout."""
        # Control frame layout
        self.control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)
        self.settings_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Status frame layout
        self.status_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=2)
        self.status_label.grid(row=0, column=0, padx=10, pady=5)
        
        # Content frame layout
        self.content_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        self.content_frame.grid_rowconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Commentary frame layout
        self.commentary_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.commentary_frame.grid_columnconfigure(0, weight=1)
        
        if CUSTOM_TK_AVAILABLE:
            self.commentary_label.grid(row=0, column=0, padx=5, pady=5)
            self.commentary_text.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        else:
            self.commentary_text.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Details frame layout
        self.details_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        if CUSTOM_TK_AVAILABLE:
            self.details_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
            self.game_phase_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
            self.assessment_label.grid(row=1, column=1, sticky="w", padx=5, pady=2)
            self.material_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
            self.king_safety_label.grid(row=2, column=1, sticky="w", padx=5, pady=2)
            self.key_factors_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        else:
            self.game_phase_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
            self.assessment_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)
            self.material_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
            self.king_safety_label.grid(row=1, column=1, sticky="w", padx=5, pady=2)
            self.key_factors_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        
        # Log frame layout
        self.log_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        self.log_frame.grid_columnconfigure(0, weight=1)
        
        if CUSTOM_TK_AVAILABLE:
            self.log_label.grid(row=0, column=0, padx=5, pady=5)
            self.log_text.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        else:
            self.log_text.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    
    def start(self):
        """Start the UI main loop."""
        self.logger.info("Starting UI")
        self.log_message("Chess Spectator UI started")
        
    def update(self):
        """Update the UI (called from main loop)."""
        try:
            self.root.update_idletasks()
            self.root.update()
        except tk.TclError:
            # Window was closed
            pass
    
    def update_status(self, status: str):
        """Update the status display."""
        if CUSTOM_TK_AVAILABLE:
            self.status_label.configure(text=f"Status: {status}")
        else:
            self.status_label.config(text=f"Status: {status}")
        
        self.log_message(f"Status: {status}")
    
    def update_analysis(
        self, 
        board_fen: str, 
        evaluation: QualitativeEvaluation, 
        commentary: str
    ):
        """Update the analysis display."""
        self.current_fen = board_fen
        self.current_evaluation = evaluation
        
        # Update commentary
        if CUSTOM_TK_AVAILABLE:
            self.commentary_text.delete("0.0", "end")
            self.commentary_text.insert("0.0", commentary)
        else:
            self.commentary_text.config(state=tk.NORMAL)
            self.commentary_text.delete("1.0", tk.END)
            self.commentary_text.insert("1.0", commentary)
            self.commentary_text.config(state=tk.DISABLED)
        
        # Update details
        self._update_analysis_details(evaluation)
        
        self.log_message("Analysis updated")
    
    def _update_analysis_details(self, evaluation: QualitativeEvaluation):
        """Update the analysis details display."""
        if CUSTOM_TK_AVAILABLE:
            self.game_phase_label.configure(text=f"Game Phase: {evaluation.game_phase}")
            self.assessment_label.configure(text=f"Assessment: {evaluation.overall_assessment}")
            self.material_label.configure(text=f"Material: {evaluation.material_situation}")
            self.king_safety_label.configure(text=f"King Safety: {evaluation.king_safety_status}")
            
            key_factors_text = f"Key Factors: {', '.join(evaluation.key_factors[:3])}"
            if len(key_factors_text) > 60:
                key_factors_text = key_factors_text[:57] + "..."
            self.key_factors_label.configure(text=key_factors_text)
        else:
            self.game_phase_label.config(text=f"Game Phase: {evaluation.game_phase}")
            self.assessment_label.config(text=f"Assessment: {evaluation.overall_assessment}")
            self.material_label.config(text=f"Material: {evaluation.material_situation}")
            self.king_safety_label.config(text=f"King Safety: {evaluation.king_safety_status}")
            
            key_factors_text = f"Key Factors: {', '.join(evaluation.key_factors[:3])}"
            if len(key_factors_text) > 60:
                key_factors_text = key_factors_text[:57] + "..."
            self.key_factors_label.config(text=key_factors_text)
    
    def log_message(self, message: str):
        """Add a message to the activity log."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        if CUSTOM_TK_AVAILABLE:
            current_text = self.log_text.get("0.0", "end")
            self.log_text.delete("0.0", "end")
            self.log_text.insert("0.0", log_entry + current_text)
        else:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert("1.0", log_entry)
            self.log_text.config(state=tk.DISABLED)
            
        # Auto-scroll to top
        if CUSTOM_TK_AVAILABLE:
            # CustomTkinter handles this automatically
            pass
        else:
            self.log_text.see("1.0")
    
    def show_error(self, message: str):
        """Show an error message."""
        messagebox.showerror("Error", message)
        self.log_message(f"ERROR: {message}")
    
    def show_info(self, message: str):
        """Show an info message."""
        messagebox.showinfo("Information", message)
        self.log_message(f"INFO: {message}")
    
    def show_settings_dialog(self, config: Any):
        """Show the settings dialog."""
        # For now, just show a simple message
        # In a full implementation, this would open a settings window
        self.show_info("Settings dialog not yet implemented")
    
    def _on_start_clicked(self):
        """Handle start button click."""
        if not self.is_analyzing and self.callbacks.on_start:
            self.is_analyzing = True
            self._update_button_states()
            asyncio.create_task(self.callbacks.on_start())
    
    def _on_stop_clicked(self):
        """Handle stop button click."""
        if self.is_analyzing and self.callbacks.on_stop:
            self.is_analyzing = False
            self._update_button_states()
            asyncio.create_task(self.callbacks.on_stop())
    
    def _on_settings_clicked(self):
        """Handle settings button click."""
        if self.callbacks.on_settings:
            asyncio.create_task(self.callbacks.on_settings())
    
    def _update_button_states(self):
        """Update button enabled/disabled states."""
        if self.is_analyzing:
            if CUSTOM_TK_AVAILABLE:
                self.start_button.configure(state="disabled")
                self.stop_button.configure(state="normal")
            else:
                self.start_button.config(state="disabled")
                self.stop_button.config(state="normal")
        else:
            if CUSTOM_TK_AVAILABLE:
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
            else:
                self.start_button.config(state="normal")
                self.stop_button.config(state="disabled")
    
    def _on_closing(self):
        """Handle window closing."""
        if self.is_analyzing:
            if messagebox.askokcancel("Quit", "Analysis is running. Do you want to quit?"):
                self.is_analyzing = False
                self.root.destroy()
        else:
            self.root.destroy()
    
    def cleanup(self):
        """Cleanup UI resources."""
        try:
            if hasattr(self, 'root'):
                self.root.quit()
                self.root.destroy()
        except Exception as e:
            self.logger.error(f"UI cleanup error: {e}")