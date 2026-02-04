# LeoBook Execution Path & Algorithm (v2.0)

## 1. High-Level Linear Overview

LeoBook executes a continuous infinite loop managed by `Leo.py`. Upon startup, it initializes CSV databases and ensures the local AI server (`Mind/llama-server`) is running. It then enters **Phase 0 (Review)** to analyze past bets by updating `site_matches.csv` and printing accuracy reports. **Phase 1 (Analysis)** launches a headless browser to scrape Flashscore, extracting match schedules, H2H history, and standings, which are fed into an in-memory `RuleEngine` to generate predictions saved to `predictions.csv`. **Phase 2 (Booking)** launches a persistent mobile browser context for Football.com, performs comprehensive session validation (login/balance/slip-clearing), and executes betting by matching predictions to site URLs, searching for markets via dynamic selectors, placing bets, and strictly verifying outcomes via booking codes and balance deductions. The cycle concludes with **Phase 3**, where the system sleeps for 6 hours. A manual **Withdrawal** module exists to securely cash out funds using a verified 4-stage process.

---

## 2. Detailed Textual Flowchart

### **STARTUP (Leo.py)**
*   **Action**: Run `python Leo.py`
*   **Subprocess**: `init_csvs()` (from `Helpers/DB_Helpers/db_helpers.py`)
    *   **Decision**: `predictions.csv` exists?
        *   **No**: Create file with headers.
    *   **Decision**: `site_matches.csv` exists?
        *   **No**: Create file with headers.
    *   **Decision**: `withdrawals.csv` exists?
        *   **No**: Create file with headers.
*   **Subprocess**: `start_ai_server()`
    *   **Action**: Check `http://127.0.0.1:8080/health`.
    *   **Decision**: Is server running?
        *   **Yes**: Return.
        *   **No**:
            *   **Action**: Locate `Mind/run_split_model.bat` (Windows) or `.sh` (Linux).
            *   **Action**: `subprocess.Popen` to launch server in new console/background.
            *   **Loop**: Poll `/health` endpoint for up to 120s until HTTP 200.
*   **Action**: Enter Main Loop (`while True`).

### **PHASE 0: REVIEW (Leo.py -> Helpers/DB_Helpers/review_outcomes.py)**
*   **Function**: `run_review_process(playwright)`
*   **Read**: `DB/site_matches.csv`.
*   **Filter**: Get matches where `booking_status` == 'booked' AND `match_time` < Current Time.
*   **Loop**: For each past match:
    *   **Action**: Determine actual result (Mock logic or future scraper implementation - currently placeholder).
    *   **Update**: `predictions.csv` -> Set `prediction_status` to 'WON' or 'LOST'.
    *   **Update**: `site_matches.csv` -> Set `result` field.
*   **Subprocess**: `print_accuracy_report()`
    *   **Read**: `predictions.csv`.
    *   **Logic**: Calculate Win/Total ratio.
    *   **Output**: Print accuracy stats to console.

### **PHASE 1: ANALYSIS (Leo.py -> Sites/flashscore.py)**
*   **Function**: `run_flashscore_analysis(playwright)`
*   **Action**: Launch Chromium (Headless).
*   **Action**: `page.goto("https://www.flashscore.com/football/")`
*   **Self-Healing**: Retry navigation 5 times if timeout/fail.
*   **Subprocess**: `fs_universal_popup_dismissal(page, "fs_home_page")`
    *   **Selector**: `fs_home_page.compliance_modal` / `onetrust_accept_btn`.
    *   **Action**: Click if visible to clear overlays.
*   **Loop**: Daily Schedule (Offset 0 to 1 days)
    *   **Action**: Click "Scheduled" tab.
        *   **Selector**: `fs_home_page.tab_scheduled`.
    *   **Subprocess**: `extract_matches_from_page(page)`
        *   **Action**: Evaluate JS on page.
        *   **Selectors (JS)**:
            *   Rows: `fs_home_page.match_rows` (e.g., `.event__match`)
            *   Teams: `.event__participant--home`, `.event__participant--away`
            *   Time: `.event__time`
            *   Links: `a.eventRowLink`
        *   **In-Memory**: Create list of `matches_data` dicts.
    *   **Filter**: Remove "Finished" matches or matches where time > Now (for today).
    *   **DB Write**: Save to `DB/schedules.csv` via `save_schedule_entry`.
    *   **Batch Processing**: `BatchProcessor.run_batch` (Concurrent Tabs)
        *   **Function**: `process_match_task(match, browser)`
        *   **Action**: `page.goto(match_link)`
        *   **Wait**: `2.0` seconds.
        *   **Subprocess**: **H2H Extraction** (`extract_h2h_data`)
            *   **Action**: Click "H2H" tab.
                *   **Selector**: `fs_match_page.tab_h2h` (e.g., `a[href="#h2h"]`).
            *   **Action**: Expand "Show more matches".
                *   **Selector**: `button:has-text('Show more matches')`.
                *   **Logic**: Click up to 2 times with sleeps.
            *   **Selectors**:
                *   Rows: `fs_h2h_tab.h2h_row`
                *   Date: `.h2h__date`
                *   Home/Away: `.h2h__participant`
                *   Score: `.h2h__result`
            *   **Validation**: Require min 3 past matches per team. Else return `False`.
        *   **Subprocess**: **Standings Extraction** (`extract_standings_data`)
            *   **Action**: Click "Standings" tab.
                *   **Selector**: `fs_match_page.tab_standings`.
            *   **Selectors**:
                *   Rows: `fs_standings_tab.table_row`
                *   Team: `.participant__participantName`
                *   Goals: `.table__cell--value`
        *   **Subprocess**: **AI Prediction** (`RuleEngine.analyze`)
            *   **Input**: `h2h_data`, `standings_data`.
            *   **Logic**: Apply rules (e.g., "Home Win if home form > 80% and away form < 20%").
            *   **Output**: Prediction dict (Type, Odds, Confidence) or `SKIP`.
        *   **Decision**: Prediction != 'SKIP'?
            *   **Yes**:
                *   **DB Write**: `save_prediction` to `DB/predictions.csv`.
                *   **Return**: `True`.
            *   **No**:
                *   **Return**: `False`.
*   **Action**: Close Browser.
*   **Subprocess**: `get_recommendations()` (from `Scripts/recommend_bets.py`)
    *   **Read**: `predictions.csv`.
    *   **Action**: Filter/Sort best bets.
    *   **Write**: Generate `DB/recommendations_{date}.txt`.

### **PHASE 2: BOOKING (Leo.py -> Sites/football_com/football_com.py)**
*   **Function**: `run_football_com_booking(playwright)`
*   **Subprocess**: `filter_pending_predictions()`
    *   **Read**: `predictions.csv`.
    *   **Filter**: Status == 'pending', Date >= Today.
    *   **In-Memory**: `pending_predictions` list.
*   **Action**: Launch Persistent Context (iPhone Emulation).
    *   **Path**: `DB/ChromeData_v3`.
*   **Subprocess**: **Step 0: Validation** (`navigator.py` -> `load_or_create_session`)
    *   **Check Login**:
        *   **Selector**: `fb_global.not_logged_in_indicator` (e.g., `.m-login-not`).
        *   **Decision**: Is visible?
            *   **Yes (Not Logged In)**: `perform_login(page)`
                *   **Action**: Wait for inputs.
                *   **Selector**: `fb_login_page.login_input_username`.
                *   **Action**: Fill Phone (Env `FB_PHONE`).
                *   **Selector**: `fb_login_page.login_input_password`.
                *   **Action**: Fill Password (Env `FB_PASSWORD`).
                *   **Selector**: `fb_login_page.login_button_submit`.
                *   **Action**: Click Login.
    *   **Check Balance** (`extract_balance`):
        *   **Selector**: `fb_global.navbar_balance` (e.g., `.navbar-balance > span`).
        *   **Logic**: Loop 3 times to get text, regex clean, parse float.
        *   **In-Memory**: `balance` (float).
    *   **Clear Slip** (`slip.py` -> `clear_bet_slip`):
        *   **Check**: `get_bet_slip_count(page)` > 0?
            *   **Yes**:
                *   **Selector**: `fb_match_page.betslip_trigger_by_attribute`. **Action**: Click (Open Slip).
                *   **Selector**: `fb_match_page.betslip_remove_all`. **Action**: Click.
                *   **Selector**: `fb_match_page.confirm_bet_button`. **Action**: Click (Confirm).
                *   **Verify**: `get_bet_slip_count` == 0.
*   **Loop**: For each Match/Prediction:
    *   **Logic**: Check Registry (`site_matches.csv`).
        *   **Decision**: Has cached URL?
            *   **Yes**: Add to `matched_urls`.
            *   **No**:
                *   **Action**: `navigate_to_schedule(page)`.
                    *   **Selector**: `fb_main_page.full_schedule_button`.
                *   **Action**: `select_target_date(page, date)`.
                    *   **Selector**: `fb_schedule_page.filter_dropdown_today`.
                    *   **Selector**: `li:has-text("Day")`.
                *   **Action**: `extract_league_matches(page)`.
                    *   **Selectors**: `fb_schedule_page.match_row`, `match_row_home_team`.
                *   **DB Write**: Append to `site_matches.csv`.
                *   **Logic**: Fuzzy Match Prediction Teams <-> Site Teams.
    *   **Subprocess**: **Place Bets** (`placement.py` -> `place_bets_for_matches`)
        *   **Loop**: matched URLs.
        *   **Decision**: `get_bet_slip_count() >= MAX_BETS`?
            *   **Yes**: Call `finalize_accumulator`.
        *   **Action**: `page.goto(match_url)`.
        *   **Action**: `neo_popup_dismissal`.
        *   **Step**: **Search Market**.
            *   **Selector**: `fb_match_page.search_icon`. **Action**: Click.
            *   **Selector**: `fb_match_page.search_input`. **Action**: Fill Market Name (e.g., "Double Chance").
            *   **Action**: Press Enter.
        *   **Step**: **Expand Market** (if collapsed).
            *   **Selector**: `fb_match_page.market_header`. **Action**: Click if exists.
        *   **Step**: **Select Outcome**.
            *   **Strategy A**: `button:text-is('1X')`.
            *   **Strategy B**: `fb_match_page.match_market_table_row` filter by text.
            *   **Action**: `robust_click(outcome)`.
        *   **Verification**:
            *   **Loop**: 3 checks.
            *   **Condition**: `new_slip_count > old_slip_count`.
            *   **Pass**: Update `prediction_status` = 'added_to_slip'.
            *   **Fail**: Update `prediction_status` = 'failed_add'.
    *   **Subprocess**: **Finalize Accumulator** (`placement.py` -> `finalize_accumulator`)
        *   **Read**: `pre_balance` via `extract_balance`.
        *   **Action**: Open Slip.
            *   **Selector**: `fb_match_page.slip_trigger_button`.
        *   **Action**: Select "Multiple" Tab.
            *   **Selector**: `fb_match_page.slip_tab_multiple`.
        *   **Action**: Set Stake.
            *   **Selector**: `fb_match_page.betslip_stake_input`. **Action**: Fill "1".
        *   **Action**: Place Bet.
            *   **Selector**: `fb_match_page.betslip_place_bet_button`.
        *   **Action**: Confirm.
            *   **Selector**: `fb_match_page.confirm_bet_button`.
        *   **Verification (Critical)**:
            *   **Wait**: Booking Code.
                *   **Selector**: `fb_match_page.booking_code_text` (via check in `extract_booking_details`).
            *   **Check**: Balance.
                *   **Logic**: `post_balance < pre_balance`.
            *   **Decision**: Logic Passes?
                *   **Yes**:
                    *   **Action**: `take_screenshot(page, "booking_success")`.
                    *   **Return**: `True`.
                *   **No**:
                    *   **Log**: "Verification FAILED".
                    *   **Return**: `False`.

### **MANUAL MODULE: WITHDRAWAL (`Sites/football_com/booker/withdrawal.py`)**
*   **Function**: `withdraw_amount(page, amount, pin)`
*   **Read**: `pre_balance` via `extract_balance`.
*   **Stage 1: Request**:
    *   **Selector**: `fb_withdraw_page.amount_input`. **Action**: Fill `amount`.
    *   **Selector**: `fb_withdraw_page.withdraw_submit_button`. **Action**: Click.
*   **Stage 2: Confirmation Data**:
    *   **Wait**: `fb_withdraw_page.confirm_dialog_wrapper`.
    *   **Read (Before Confirm)**:
        *   `fb_withdraw_page.confirm_amount_value` -> `amount_confirmed`.
        *   `fb_withdraw_page.confirm_bank_value` -> `bank_confirmed`.
        *   `fb_withdraw_page.confirm_account_value` -> `account_confirmed`.
    *   **Selector**: `fb_withdraw_page.confirm_confirm_button`. **Action**: Click.
*   **Stage 3: Security**:
    *   **Selector**: `fb_withdraw_page.pin_input_fields`. **Action**: Fill `pin` (digit by digit).
    *   **Selector**: `fb_withdraw_page.pin_confirm_button`. **Action**: Click.
*   **Stage 4: Verification**:
    *   **Wait**: `fb_withdraw_page.success_dialog_wrapper` (Timeout 25s).
    *   **Check**: `fb_withdraw_page.success_title` contains "Pending Request".
    *   **Check**: `post_balance` approx equals `pre_balance - amount`.
*   **DB Write**:
    *   **Condition**: Success verified.
    *   **Action**: Append row to `DB/withdrawals.csv` (Timestamp, Amount, Bank, Reason).

### **PHASE 3: CYCLE COMPLETION (Leo.py)**
*   **Action**: Print "Cycle Complete".
*   **Action**: `asyncio.sleep(CYCLE_WAIT_HOURS * 3600)` (Default 6 hours).
*   **Loop**: Return to Phase 0.

---

## 3. Data Flow Summary Table

| Data Entity | Source Module / Function | Storage Location | Key Operations |
| :--- | :--- | :--- | :--- |
| **Schedule** | `flashscore.py` / `extract_matches_from_page` | `DB/schedules.csv` | Write (Daily) |
| **History (H2H)** | `flashscore.py` / `extract_h2h_data` | Memory (for Analysis) | Read (Analysis) |
| **Predictions** | `RuleEngine.py` / `analyze` | `DB/predictions.csv` | Write (Phase 1), Read/Update (Phase 0, 2) |
| **Site Matches** | `extractor.py` / `extract_league_matches` | `DB/site_matches.csv` | Write (New), Read (Cache) |
| **Session** | `navigator.py` / `perform_login` | `DB/Auth/storage_state.json`| Write (Login), Read (Startup) |
| **Withdrawals** | `withdrawal.py` / `withdraw_amount` | `DB/withdrawals.csv` | Write (Append on Success) |
| **Selectors** | `knowledge.json` | JSON File | Read (SelectorManager), Update (Auto) |
| **Balance** | `navigator.py` / `extract_balance` | Memory / Console | Read (Validation, Verification) |
