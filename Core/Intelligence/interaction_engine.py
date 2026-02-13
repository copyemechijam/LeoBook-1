# interaction_engine.py: Resilient UI interaction with auto-healing.
# Refactored for Aggressive Resiliency (v2.8)

import asyncio
from typing import Callable, Any, Optional
from .visual_analyzer import VisualAnalyzer
from .selector_db import knowledge_db

async def execute_smart_action(
    page: Any,
    context_key: str,
    element_key: str,
    action_fn: Callable[[str], Any],
    max_retries: int = 3
) -> Any:
    """
    Wraps browser actions that require a selector in a resilient retry loop.
    If the action fails (e.g., selector is stale or missing), it triggers
    aggressive AI discovery (VisualAnalyzer) and retries the action.

    Args:
        page: Playwright page object.
        context_key: The knowledge.json context (e.g., 'fb_match_page').
        element_key: The specific element key (e.g., 'bet_slip_book_bet_button').
        action_fn: A lambda or function taking a selector string and returning a coroutine.
                   Example: lambda sel: page.click(sel)
        max_retries: Number of AI-healing attempts before giving up.

    Returns:
        The result of the action_fn if successful.

    Raises:
        The original exception if all retries fail.
    """
    last_error = None
    
    for attempt in range(max_retries + 1):
        # 1. Get the current selector from the local database
        # We access knowledge_db directly for speed, as it's kept in sync.
        selector = knowledge_db.get(context_key, {}).get(element_key)
        
        # 2. If selector is missing, trigger an immediate discovery
        if not selector:
            print(f"    [Smart Action] Selector '{element_key}' missing in '{context_key}'. Triggering Discovery...")
            await VisualAnalyzer.analyze_page_and_update_selectors(
                page, 
                context_key, 
                force_refresh=True, 
                info=f"Missing selector: {element_key}"
            )
            selector = knowledge_db.get(context_key, {}).get(element_key)

        if selector:
            try:
                # 3. Attempt to perform the action
                # This could be a click, fill, hover, etc.
                return await action_fn(selector)
            except Exception as e:
                last_error = e
                # Trap common selector errors (Timeout, Not Found, Not Visible)
                print(f"    [Smart Action] Action failed for '{element_key}' (Attempt {attempt+1}/{max_retries+1}): {e}")
        
        # 4. If we reach here, either the selector was missing or the action failed.
        # We trigger the Aggressive AI Discovery to refresh the knowledge base.
        if attempt < max_retries:
            print(f"    [Smart Action] Healing context '{context_key}' for '{element_key}'...")
            await VisualAnalyzer.analyze_page_and_update_selectors(
                page, 
                context_key, 
                force_refresh=True, 
                info=f"Action FAILED on '{element_key}'. Reason: {str(last_error)}"
            )
            # Brief pause to allow DOM to settle after possible discovery interactions
            await asyncio.sleep(1.0)

    # 5. Exhausted all retries
    print(f"    [Smart Action ERROR] Failed '{element_key}' in '{context_key}' after {max_retries} AI-healing cycles.")
    if last_error:
        raise last_error
    raise RuntimeError(f"Could not find selector or perform action for '{element_key}'")
