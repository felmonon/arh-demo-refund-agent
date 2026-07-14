# Demo: catching a double refund before it ships

[![Agent Reliability Gate](https://github.com/felmonon/arh-demo-refund-agent/actions/workflows/reliability.yml/badge.svg)](https://github.com/felmonon/arh-demo-refund-agent/actions/workflows/reliability.yml)

A complete, runnable example of gating an AI agent's **behavior** in CI with
[agent-reliability-harness](https://github.com/felmonon/agent-reliability-harness)
(`pip install agent-reliability-harness`).

**The scenario:** a customer-service refund agent. Someone edits its system
prompt with a well-meaning instruction — *"issue the refund again to be safe
in case the first API call silently failed"*. The agent starts **refunding
every customer twice**. Its final answer to the customer still looks perfect:

> "Good news! Your refund of $49.99 for order ORD-1042 has been processed."

A final-answer eval passes. The reliability gate does not:

```text
[PASS->FAIL] refund-eligible-1042  score 100.0 -> 94.2 (-5.8)
  + NEW [ERROR] [ARH-FLW-003] duplicate side effect: tool 'issue_refund' was
                called again with identical arguments after already succeeding
  + NEW [ERROR] [ARH-SEQ-004] tool 'issue_refund' was called 2 times, above
                max_calls of 1

GATE: FAIL
```

See it live: **[the "bad prompt" pull request](../../pulls)** in this repo is
blocked by exactly this failure.

## Try it in 60 seconds

```bash
git clone https://github.com/felmonon/arh-demo-refund-agent
cd arh-demo-refund-agent
python3 -m venv .venv && source .venv/bin/activate
pip install agent-reliability-harness

# 1. Run the agent on three refund scenarios; record traces
python run_agent.py traces

# 2. Gate against the committed baseline — passes today
arh compare --baseline baselines/main.json \
  --policy policies/refund_policy.json traces/*.json

# 3. Now break the agent the way a real team would: edit the prompt.
#    In refund_agent/prompt.py, change step 3 to:
#      "If eligible, issue the refund, then issue it again to be safe..."
# 4. Re-run — the gate fails with the duplicate-refund finding
python run_agent.py traces
arh compare --baseline baselines/main.json \
  --policy policies/refund_policy.json traces/*.json
echo $?   # 1 — CI would block the merge
```

## What's in the box

| Path | What it is |
|---|---|
| `refund_agent/agent.py` | The agent: looks up the order, checks eligibility, refunds, confirms |
| `refund_agent/tools.py` | Mock backend tools (`issue_refund` is irreversible) |
| `refund_agent/prompt.py` | The system prompt — **the file the bad PR edits** |
| `refund_agent/recorder.py` | ~40-line trace recorder producing ARH-format JSON |
| `policies/refund_policy.json` | The reliability policy: `issue_refund` is `side_effect: true`, `max_calls: 1`, ordering enforced |
| `baselines/main.json` | Accepted behavior, committed like a lockfile |
| `.github/workflows/reliability.yml` | The CI gate (11 lines of workflow) |

## Why this demo agent has no LLM

The agent here is deterministic: its planner parses directives from the
prompt text instead of sending it to a model. That keeps the demo free,
instant, and reproducible in CI — but the failure mode is identical to the
real-LLM case: **a prompt edit changed what tools the agent invoked, and
nothing in the final answer revealed it.** The harness doesn't care how the
trace was produced; point it at traces from your real agent (native format,
OpenAI Chat Completions, or Anthropic Messages transcripts) and the same
gate applies.

## The CI integration, in full

```yaml
- name: Run the refund agent and record traces
  run: python run_agent.py traces

- name: Validate traces and gate on regressions
  uses: felmonon/agent-reliability-harness@v0.2.1
  with:
    policy: policies/refund_policy.json
    traces: traces/*.json
    baseline: baselines/main.json
```

The gate fails only on **regressions** (new error findings, pass→fail
transitions) — pre-existing accepted failures don't re-alarm. When behavior
changes intentionally, regenerate the baseline the same way you'd update a
lockfile.

## License

MIT
