import csv
import asyncio
from datetime import datetime
from pathlib import Path
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from Neo.selector_manager import SelectorManager
from .ui import robust_click
# Adjusted import: navigator is in the parent directory (Sites/football_com)
from ..navigator import extract_balance

WITHDRAWALS_CSV = Path("DB/withdrawals.csv")


async def check_and_perform_withdrawal(page: Page, current_balance: float, last_win_amount: float = 0):
    """
    Evaluates withdrawal rules and executes if valid.
    Rules:
    1. Min withdrawal: N500
    2. Max withdrawal: Min(30% of Total Balance, 50% of Latest Win)
       (If last_win_amount is 0/unknown, use 30% balance rule only)
    """
    MIN_WITHDRAWAL = 500
    
    # 1. Calculate Candidate Amounts
    cand_balance_rule = current_balance * 0.30
    cand_win_rule = last_win_amount * 0.50 if last_win_amount > 0 else cand_balance_rule
    
    # Take the smaller of the two caps (Conservative approach)
    max_allowable = min(cand_balance_rule, cand_win_rule)
    
    # Final Amount Check
    if max_allowable < MIN_WITHDRAWAL:
        print(f"    [Withdrawal] Skipped. Max allowable (N{max_allowable:.2f}) < Min Limit (N{MIN_WITHDRAWAL})")
        return False
        
    final_amount = int(max_allowable) # Withdrawals usually integer
    print(f"    [Withdrawal] Initiating withdrawal of N{final_amount} (Rules: 30% Bal or 50% Win)")
    
    return await _execute_withdrawal_flow(page, str(final_amount))

async def _execute_withdrawal_flow(page: Page, amount: str = "100", pin: str = "1234"):
    """
    Internal flow: Enter amount -> Confirm -> PIN -> Verify
    """
    pre_balance = await extract_balance(page)
    print(f"    [Withdraw Flow] Starting. Pre-balance: {pre_balance}")


    # --- Stage 1: Enter amount & submit ---
    amount_sel = SelectorManager.get_selector("fb_withdraw_page", "amount_input")
    await page.fill(amount_sel, amount)

    submit_sel = SelectorManager.get_selector("fb_withdraw_page", "withdraw_submit_button")
    await page.wait_for_selector(f"{submit_sel}:not(.is-disabled)", timeout=15000)
    await robust_click(page.locator(submit_sel).first, page)

    # --- Stage 2: Confirmation dialog - extract data first ---
    await page.wait_for_selector(
        SelectorManager.get_selector("fb_withdraw_page", "confirm_dialog_wrapper"),
        timeout=15000
    )

    # Extract data **before** confirming
    amount_confirmed = await page.locator(
        SelectorManager.get_selector("fb_withdraw_page", "confirm_amount_value")
    ).inner_text()

    bank_confirmed = await page.locator(
        SelectorManager.get_selector("fb_withdraw_page", "confirm_bank_value")
    ).inner_text()

    account_confirmed = await page.locator(
        SelectorManager.get_selector("fb_withdraw_page", "confirm_account_value")
    ).inner_text()

    account_name_confirmed = await page.locator(
        SelectorManager.get_selector("fb_withdraw_page", "confirm_account_name_value")
    ).inner_text()

    print(f"[Withdraw Confirm] Amount: {amount_confirmed} | Bank: {bank_confirmed}")
    print(f"                 Account: {account_confirmed} | Name: {account_name_confirmed}")

    # Confirm
    confirm_btn_sel = SelectorManager.get_selector("fb_withdraw_page", "confirm_confirm_button")
    await robust_click(page.locator(confirm_btn_sel).first, page)

    # --- Stage 3: Enter PIN ---
    pin_fields_sel = SelectorManager.get_selector("fb_withdraw_page", "pin_input_fields")
    pin_fields = page.locator(pin_fields_sel)

    # Wait for pin fields to be visible
    await page.wait_for_selector(pin_fields_sel, timeout=10000)

    for i, digit in enumerate(pin):
        await pin_fields.nth(i).fill(digit)
        await asyncio.sleep(0.3)  # small delay to mimic human

    pin_confirm_sel = SelectorManager.get_selector("fb_withdraw_page", "pin_confirm_button")
    await page.wait_for_selector(f"{pin_confirm_sel}:not(.is-disabled)", timeout=10000)
    await robust_click(page.locator(pin_confirm_sel).first, page)

    # --- Stage 4: Wait for success dialog "Pending Request" ---
    try:
        await page.wait_for_selector(
            SelectorManager.get_selector("fb_withdraw_page", "success_dialog_wrapper"),
            timeout=25000
        )

        success_title = await page.locator(
            SelectorManager.get_selector("fb_withdraw_page", "success_title")
        ).inner_text()

        if "Pending Request" not in success_title:
            raise Exception("Success dialog appeared but title is not 'Pending Request'")

        print("[Withdraw] Success dialog detected -> Pending Request")

    except PlaywrightTimeoutError:
        raise Exception("No 'Pending Request' dialog appeared after PIN -> likely failed")

    # --- Final Verification: Balance must decrease by exactly the amount ---
    await asyncio.sleep(3)  # give backend time to process
    post_balance = await extract_balance(page)

    withdrawn_amount = float(amount_confirmed.replace(",", ""))
    expected_post = pre_balance - withdrawn_amount

    if abs(post_balance - expected_post) > 0.1:  # small tolerance for rounding
        raise Exception(
            f"Balance verification failed. "
            f"Pre: {pre_balance}, Expected post: {expected_post}, Actual: {post_balance}"
        )

    print(f"[Withdraw] Balance verification OK: {pre_balance} -> {post_balance}")

    # --- Save successful withdrawal to CSV ---
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "amount": amount_confirmed,
        "bank": bank_confirmed,
        "account_number": account_confirmed,
        "account_name": account_name_confirmed,
        "balance_before": pre_balance,
        "balance_after": post_balance,
        "reason": reason
    }

    WITHDRAWALS_CSV.parent.mkdir(parents=True, exist_ok=True)
    file_exists = WITHDRAWALS_CSV.exists()

    with open(WITHDRAWALS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=record.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)

    print(f"[Withdraw] Successfully saved record to {WITHDRAWALS_CSV}")

    # Optional: click "Transaction" or "Home" button to leave dialog
    try:
        await page.locator(
            SelectorManager.get_selector("fb_withdraw_page", "success_home_btn")
        ).click(timeout=5000)
    except:
        pass  # not critical

