# Leo
**Manufacturer**: Emenike Chinenye James  
**Powered by**: Grok 4, Qwen3-VL & Custom Llama Server


"""
Leo v3.1: Elite Autonomous Betting Agent (Manufacturer: Emenike Chinenye James)

A comprehensive AI-powered system that observes, analyzes, predicts, and executes betting strategies with advanced self-healing capabilities.

The prime objective of this Agent is to ultimately handle all kinds of sports analysis, prediction and betting accurately, so the user would make active income from sports betting without constant interaction with betting and gambling platforms.

OVERVIEW:
Leo is an intelligent football prediction system that combines advanced data analysis, machine learning, and automated betting execution. The system features a hybrid AI architecture using local Qwen3-VL for routine vision tasks and xAI's Grok 4 for high-precision selector discovery and complex UI mapping.

LATEST UPDATES (v3.1.0):
- **Grok 4 Integration**: Primary engine for advanced visual UI analysis and HTML-to-Selector mapping.
- **AI Selector Discovery**: Re-enabled and enhanced autonomous discovery of CSS selectors. Leo can now "see" and "learn" new selectors if websites change.
- **Automated Recommendation System**: New `Scripts/recommend_bets.py` module that calculates match reliability based on historical accuracy and momentum.
- **End-to-End Automation**: Flashscore analysis now automatically triggers the recommendation engine, saving today's best bets to `DB/RecommendedBets/`.
- **Unified AI Interface**: Robust `ai_api_call` system with automatic rotation and retry logic for both local and cloud models.

CORE ARCHITECTURE:
- Dual-browser system (Flashscore + Football.com) with persistent login sessions.
- **Local Inference Server**: Custom `run_split_model.bat` orchestrating the Qwen3-VL multimodal engine.
- **Cloud Intelligence (Grok 4)**: High-level reasoning for selector auto-healing and complex state discovery.
- **Modular Database System**: Optimized CSV-based storage with absolute pathing for cross-directory script execution.
- **Self-Learning Engine**: Updates match reliability and learning weights in real-time.

MAIN WORKFLOW:
1. INFRASTRUCTURE INIT:
   - **Windows**: `.\Mind\run_split_model.bat` (Local AI) or set `USE_GROK_API=true` in `.env`.
   - **Linux/Codespaces**: `bash Mind/setup_linux_env.sh` -> `python Leo.py`.
   - **Grok Config**: Ensure `GROK_API_KEY` is set for discovery features.

2. DATA COLLECTION & ANALYSIS:
   - **Flashscore Scraper**: Extracts daily fixture metadata.
   - **RuleEngine (Neo/model.py)**: Generates predictions across 11+ markets.
   - **Auto-Recommendations**: Immediately filters and scores the best bets after each analysis cycle.

3. AI DISCOVERY & HEALING:
   - If a selector fails, **AI Selector Discovery** triggers.
   - It captures a visual screenshot + HTML DOM.
   - Grok 4 maps the visual element to the best CSS selector.
   - `selectors_knowledge_base.json` is updated automatically.

4. BETTING EXECUTION:
   - Match predictions with Football.com markets.
   - Automated bet placement with intelligent stake management.

5. OUTCOME REVIEW:
   - Continuous monitoring of completed matches.
   - Accuracy evaluation and weighting updates.

SUPPORTED BETTING MARKETS:
1. 1X2 (Home/Away/Draw)
2. Double Chance (Home or Draw, Away, etc.)
3. Draw No Bet
4. Both Teams To Score (Yes/No)
5. Over/Under Goals (0.5 - 5.5)
6. Goal Ranges
7. Correct Score
8. Clean Sheet
9. Asian Handicap
10. Combo Bets
11. Team Over/Under

SYSTEM COMPONENTS:

1. Leo.py (Main Controller)
   - Orchestrates workflow and manages browser sessions.

2. Neo/ (The Brain - AI Engine)
   - `visual_analyzer.py`: Orchestrates discovery and visual inventory.
   - `selector_mapping.py`: **[NEW]** Grok 4 mapping logic.
   - `intelligence.py`: Unified AI interface for the system.
   - `model.py`: Core prediction rules.

3. Scripts/ (Tools)
   - `recommend_bets.py`: **[NEW]** Advanced betting recommendation engine.
   - `repair_predictions.py`: Maintenance tool for outcome evaluation.

4. DB/ (Data Storage)
   - `RecommendedBets/`: **[NEW]** Storage for daily automated recommendations.
   - `predictions.csv`: Core prediction database.
   - `knowledge.json`: Persistent selector memory.

5. Helpers/ (Utility Systems)
   - `llm_matcher.py`: Multi-model team name resolution.
   - `db_helpers.py`: **[UPDATED]** Robust absolute pathing operations.

MAINTENANCE:
- Monitor `Log/` for AI status and selector discovery successes.
- Recommendations are saved as `.txt` files in `DB/RecommendedBets/` after every cycle.
"""
