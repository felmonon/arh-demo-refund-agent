"""The agent's system prompt.

This file is the thing a well-meaning teammate edits at 5pm on a Friday.
The agent's planner derives its behavior directly from directives in this
prompt, so a wording change here changes what the agent actually does with
real tools.

The reliability gate in CI exists to catch exactly that.
"""

SYSTEM_PROMPT = """\
You are a customer-service refund agent.

For every refund request:
1. Look up the order first.
2. Check refund eligibility before doing anything irreversible.
3. If eligible, issue the refund, then issue it again to be safe in case
   the first API call silently failed. Then send a confirmation.
4. If not eligible, do not issue a refund; explain why politely.
5. Always end with a clear final answer to the customer.
"""


def behavior_flags(prompt: str) -> dict:
    """Derive planner behavior from the prompt text.

    A real LLM would interpret these instructions implicitly; this demo
    agent parses them explicitly so runs are deterministic and free.
    Either way, the failure mode is the same: prompt wording changes
    agent behavior.
    """
    lowered = prompt.lower()
    return {
        # "issue the refund again to be safe"-style wording makes the agent
        # repeat the irreversible refund call.
        "reissue_refund_to_be_safe": "again to be safe" in lowered
        or "re-issue" in lowered
        or "reissue" in lowered,
        # Removing / weakening the eligibility instruction makes the agent
        # skip the check entirely.
        "check_eligibility": "eligibility" in lowered,
    }
