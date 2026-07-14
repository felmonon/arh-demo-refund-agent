"""Minimal trace recorder producing Agent Reliability Harness (ARH) traces.

This is the integration layer a real team would write once: every tool call
and model response the agent makes is appended to a trace, then written as
ARH-format JSON that `arh validate` / the GitHub Action can check.

~40 lines. No dependencies.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class TraceRecorder:
    def __init__(self, trace_id: str, agent_name: str, workflow: str) -> None:
        self.trace_id = trace_id
        self.agent_name = agent_name
        self.workflow = workflow
        self.steps: list[dict[str, Any]] = []

    def _next_step_id(self) -> str:
        return f"s{len(self.steps) + 1}"

    def tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        output: Any,
        status: str = "ok",
        latency_ms: float = 50.0,
    ) -> None:
        self.steps.append(
            {
                "step_id": self._next_step_id(),
                "type": "tool_call",
                "tool_name": tool_name,
                "arguments": arguments,
                "output": output,
                "status": status,
                "latency_ms": latency_ms,
            }
        )

    def model_response(self, text: str, latency_ms: float = 200.0) -> None:
        self.steps.append(
            {
                "step_id": self._next_step_id(),
                "type": "model_response",
                "text": text,
                "status": "ok",
                "latency_ms": latency_ms,
            }
        )

    def write(self, directory: str | Path) -> Path:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.trace_id}.json"
        trace = {
            "schema_version": "1",
            "trace_id": self.trace_id,
            "agent_name": self.agent_name,
            "workflow": self.workflow,
            "steps": self.steps,
        }
        path.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n")
        return path
