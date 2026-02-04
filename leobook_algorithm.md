# LeoBook Execution Path & Algorithm (v2.6)

## 1. High-Level Linear Overview

LeoBook executes a continuous infinite loop managed by `Leo.py`. Upon startup, it initializes CSV databases and sets up a global **State Dictionary** for cycle-long awareness. It then enters **Phase 0 (Review)** to analyze past bets and print accuracy reports. **Phase 1 (Analysis)** scrapes Flashscore to generate predictions saved to `predictions.csv`. **Phase 2 (Booking)** follows a strict **Harvest -> Execute** strategy for Football.com: it first gathers booking codes for each match (Harvest) and then builds a multi-bet accumulator using these codes (Execute). This phase includes robust **Force Slip Clearing** with a fatal error path to ensure a clean state. **AI Server** usage is now lazy-loaded, starting only when URL resolution (Cache -> LLM) requires it. The system enforces strict **Stake Rules** (Min N1, Max 50% balance) and **Withdrawal Rules** (Min N500, Max conservative caps). The cycle concludes with **Phase 3**, sleeping for 6 hours.

---

## 2. Detailed Textual Flowchart

### **STARTUP (Leo.py)**
*   **Action**: Run `python Leo.py`
*   **Initialization**: `state = {}` (Global tracking for progress, balance, and errors).
*   **Helper**: `log_state(phase, action, next_step)` (Updates `state` and logs with timestamps).
*   **Subprocess**: `init_csvs()`
    *   **Action**: Ensure `predictions.csv`, `football_com_matches.csv`, and `withdrawals.csv` exist with correct headers (including new Phase 2 fields: `booking_code`, `booking_url`).
*   **Action**: Enter Main Loop (`while True`).

### **PHASE 0: REVIEW (Leo.py -> Helpers/DB_Helpers/review_outcomes.py)**
*   **Action**: `log_state("Phase 0", "Reviewing Outcomes")`.
*   **Function**: `run_review_process(playwright)`
*   **Read**: `DB/football_com_matches.csv`.
*   **Update**: Mark WON/LOST in `predictions.csv` and generate accuracy report.

### **PHASE 1: ANALYSIS (Leo.py -> Sites/flashscore.py)**
*   **Action**: `log_state("Phase 1", "Generating Predictions")`.
*   **Function**: `run_flashscore_analysis(playwright)`
*   **Subprocess**: Extract match data (H2H, Standings) and run `RuleEngine` to save 'pending' predictions to `predictions.csv`.

### **PHASE 2: BOOKING (Leo.py -> Sites/football_com/football_com.py)**
*   **Action**: `log_state("Phase 2", "Booking bets")`.
*   **Verification**: Filter pending future predictions.
*   **Startup Check**: `_ensure_ai_server_if_needed()`
    *   **Logic**: Only starts AI server if matching fails cache and requires LLM analysis.
*   **Step 1: Session & Force Slip Clear**
    *   **Function**: `force_clear_slip(page)`
    *   **Logic**: Retry clearing 3 times. If still dirty, delete `storage_state.json` and raise `FatalSessionError` (forces hard restart).
*   **Step 2: URL Resolution (Matcher)**
    *   **Function**: `match_predictions_with_site(page, predictions, date)`
    *   **Logic**: Cache-first lookup -> Scrape schedule -> LLM Semantic Matching.
*   **Step 3: PHASE 2a - HARVEST (booking_code.py)**
    *   **Function**: `book_single_match(page, match_dict, prediction)`
    *   **Action**: Navigate to match URL -> Select Outcome -> Click "Book" -> Extract `booking_code` and `booking_url`.
    *   **Validation**: Odds must be >= 1.20.
    *   **Update**: Save harvested code to `football_com_matches.csv`.
*   **Step 4: PHASE 2b - EXECUTE (placement.py)**
    *   **Function**: `place_multi_bet_from_codes(page, harvested_codes, balance)`
    *   **Logic**: 
        1. Inject codes via URL params: `?shareCode=CODE1,CODE2...`
        2. `force_clear_slip(page)` to ensure clean slate.
        3. Navigate to injected URL.
        4. Calculate Stake: `Min(N1, 0.01 * balance)` and cap at `max(N1, 0.50 * balance)`.
        5. Click "Place Bet" -> "Confirm".
    *   **Verification**: Ensure balance decreased by exactly the stake amount.

### **WITHDRAWAL MODULE (withdrawal.py)**
*   **Function**: `check_and_perform_withdrawal(page, current_balance, last_win_amount)`
*   **Enforcement**:
    *   **Min Withdrawal**: ₦500.
    *   **Max Withdrawal**: `Min(30% of Total Balance, 50% of Latest Win)`.
*   **Verification**: Confirm "Pending Request" dialog and balance reduction before saving to `DB/withdrawals.csv`.

### **PHASE 3: CYCLE COMPLETION (Leo.py)**
*   **Action**: `log_state("Cycle End", "Sleeping")`.
*   **Action**: `asyncio.sleep(CYCLE_WAIT_HOURS * 3600)`.

---

## 3. Data Flow Summary Table

| Data Entity | Primary Storage | Key Logic |
| :--- | :--- | :--- |
| **Predictions** | `DB/predictions.csv` | Status: `pending` -> `added_to_slip` -> `WON/LOST`. |
| **Site Matches** | `DB/football_com_matches.csv`| Stores `booking_code`, `booking_url`, and `match_url`. |
| **State** | In-Memory (`Leo.state`) | Tracks `last_balance`, `current_phase`, and `error_count`. |
| **Selectors** | `DB/knowledge.json` | Auto-healed via `SelectorManager.get_selector_auto`. |
| **Session** | `DB/ChromeData_v3` | Validated via `force_clear_slip`. |
| **Large Models** | `Mind/*.gguf` | Ignored by Git; managed locally for LLM Matching. |
