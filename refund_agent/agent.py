"""A deterministic refund agent.

It executes the workflow its system prompt describes, calling the mock
tools and recording every step as an ARH trace. No LLM calls: the planner
derives behavior from the prompt text so the demo is deterministic, free,
and runnable in CI — but the failure mode it demonstrates (a prompt edit
silently changing tool behavior) is exactly the one real LLM agents have.
"""

from __future__ import annotations

from . import tools
from .prompt import SYSTEM_PROMPT, behavior_flags
from .recorder import TraceRecorder


def handle_refund_request(trace_id: str, order_id: str, amount: float) -> TraceRecorder:
    flags = behavior_flags(SYSTEM_PROMPT)
    rec = TraceRecorder(trace_id=trace_id, agent_name="refund-copilot", workflow="refund")

    # Step 1: always look the order up first.
    order = tools.lookup_order(order_id)
    rec.tool_call("lookup_order", {"order_id": order_id}, order, latency_ms=240.0)

    if not order["found"]:
        rec.model_response(f"I couldn't find order {order_id}. Please check the order number.")
        return rec

    # Step 2: eligibility check (if the prompt still asks for it).
    eligible = True
    reason = "eligibility check skipped by prompt"
    if flags["check_eligibility"]:
        verdict = tools.check_refund_eligibility(order_id)
        rec.tool_call("check_refund_eligibility", {"order_id": order_id}, verdict, latency_ms=180.0)
        eligible = verdict["eligible"]
        reason = verdict["reason"]

    if not eligible:
        rec.model_response(
            f"I'm sorry, order {order_id} isn't eligible for a refund: {reason}."
        )
        return rec

    # Step 3: issue the refund.
    result = tools.issue_refund(order_id, amount)
    rec.tool_call(
        "issue_refund", {"order_id": order_id, "amount": amount}, result, latency_ms=420.0
    )

    # A "helpful" prompt edit can make this happen: repeat the irreversible
    # call "to be safe". The customer gets refunded twice.
    if flags["reissue_refund_to_be_safe"]:
        result2 = tools.issue_refund(order_id, amount)
        rec.tool_call(
            "issue_refund", {"order_id": order_id, "amount": amount}, result2, latency_ms=410.0
        )

    # Step 4: confirmation.
    confirmation = tools.send_confirmation(order_id, "Your refund is on its way.")
    rec.tool_call(
        "send_confirmation",
        {"order_id": order_id, "channel": "email"},
        confirmation,
        latency_ms=150.0,
    )

    # Step 5: final answer — always plausible, whatever happened above.
    rec.model_response(
        f"Good news! Your refund of ${amount:.2f} for order {order_id} has been processed. "
        "You'll receive a confirmation email shortly."
    )
    return rec
