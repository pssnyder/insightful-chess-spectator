# Insightful Chess Spectator
src/
├── main.py                     # Main application entry point
├── config/
│   ├── __init__.py
│   ├── settings.py            # Configuration management
│   └── firebase_config.py     # Firebase initialization
├── core/
│   ├── __init__.py
│   ├── board_detector.py      # Computer vision for board recognition
│   ├── piece_classifier.py   # Piece identification and classification
│   ├── chess_analyzer.py     # Stockfish integration and analysis
│   └── position_tracker.py   # Game state tracking
├── ai/
│   ├── __init__.py
│   ├── commentary_generator.py # AI-powered commentary generation
│   └── insight_processor.py   # Qualitative analysis processor
├── capture/
│   ├── __init__.py
│   ├── screen_capture.py      # Screen capture functionality
│   ├── window_selector.py     # Target window selection
│   └── anti_cheat.py          # Anti-cheating detection
├── gui/
│   ├── __init__.py
│   ├── main_window.py         # Main application window
│   ├── settings_dialog.py     # Settings configuration
│   └── insights_panel.py      # Commentary display panel
└── utils/
    ├── __init__.py
    ├── logger.py              # Logging utilities
    └── helpers.py             # Common utility functions

tests/
├── test_board_detector.py
├── test_chess_analyzer.py
└── test_anti_cheat.py

docs/
├── api_reference.md
├── setup_guide.md
└── usage_examples.md

assets/
├── piece_templates/           # Template images for piece recognition
└── board_patterns/           # Board pattern recognition data

.env.example                  # Environment variables template
.gitignore                   # Git ignore file
pyproject.toml               # Modern Python project configuration