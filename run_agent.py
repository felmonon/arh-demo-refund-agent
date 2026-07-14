"""Run every scenario through the refund agent and write ARH traces.

Usage:  python run_agent.py [output_dir]
"""

import json
import sys
from pathlib import Path

from refund_agent.agent import handle_refund_request

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("traces")
scenarios = json.loads(Path("scenarios/requests.json").read_text())

for sc in scenarios:
    rec = handle_refund_request(sc["trace_id"], sc["order_id"], sc["amount"])
    path = rec.write(OUT)
    print(f"wrote {path} ({len(rec.steps)} steps)")
