import os
import json
import glob

# Resolve data/ and docs/ relative to repo root (works from any cwd, incl. the MCP server).
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _p(rel): return os.path.join(ROOT, rel)

def _metrics(): return json.load(open(_p("data/metrics.json")))
def _deploys(): return json.load(open(_p("data/deploys.json")))


def list_services():
    return ", ".join(_metrics().keys())

# Thresholds give the tool a sense of SCALE, so it doesn't call a trivial wiggle "rising".
# warn/crit come from the runbooks (e.g. checkout-5xx: ">2% sustained error rate is an incident").
THRESHOLDS = {
    "error_rate":     {"warn": 1.0, "crit": 2.0, "unit": "%"},
    "p99_latency_ms": {"warn": 500, "crit": 1000, "unit": "ms"},
}

def get_metric(service, name):
    vals = _metrics().get(service, {}).get(name)
    if not vals:
        return f"No metric '{name}' for '{service}'."
    latest, first, delta = vals[-1], vals[0], vals[-1] - vals[0]
    t = THRESHOLDS.get(name)
    if t:
        unit = t["unit"]
        status = "CRITICAL" if latest >= t["crit"] else "WARNING" if latest >= t["warn"] else "OK"
        # Only call it a real move if the change is significant vs the warn threshold,
        # so 0.1->0.2% or 180->200ms reads as "stable", not "rising".
        if abs(delta) < t["warn"] / 2:
            trend = "stable"
        else:
            trend = "rising" if delta > 0 else "falling"
        return (f"{service}.{name} recent={vals} latest={latest}{unit} "
                f"(Δ{delta:+g}{unit} from {first}{unit}); trend={trend}; "
                f"status={status} (warn≥{t['warn']}{unit}, crit≥{t['crit']}{unit})")
    # Unknown metric: fall back to the simple description (no thresholds defined).
    trend = "rising" if delta > 0 else "stable/falling"
    return f"{service}.{name} recent={vals} (latest={latest}, {trend})"

def recent_deploys(service):
    ds = _deploys().get(service, [])
    return json.dumps(ds) if ds else f"No deploys for '{service}'."

def search_logs(query, service=None):
    out = []
    q = query.lower()
    for line in open(_p("data/logs.jsonl")):
        rec = json.loads(line)
        # Match the query against the message OR the level, so a search for "ERROR"
        # finds ERROR-level lines even when the word isn't in the message text.
        hit = q in rec["msg"].lower() or q in rec["level"].lower()
        if hit and (not service or rec["service"] == service):
            out.append(f"{rec['at']} {rec['level']} {rec['service']}: {rec['msg']}")
    return "\n".join(out) or "No matching logs."

def get_runbook(name):
    for path in glob.glob(_p("docs/*.md")):
        if name.lower() in os.path.basename(path).lower():
            return open(path, encoding="utf-8").read()
    return "Runbook not found."


# Neutral tool registry: JSON-Schema params (provider-agnostic) + the function to run.
TOOLS = [
    {"name": "list_services", "description": "List known services.",
     "parameters": {"type": "object", "properties": {}}, "fn": list_services},
    {"name": "get_metric", "description": "Get recent values + trend for a service metric (e.g. error_rate, p99_latency_ms).",
     "parameters": {"type": "object",
        "properties": {"service": {"type": "string"}, "name": {"type": "string"}},
        "required": ["service", "name"]}, "fn": get_metric},
    {"name": "recent_deploys", "description": "List recent deploys for a service.",
     "parameters": {"type": "object",
        "properties": {"service": {"type": "string"}}, "required": ["service"]}, "fn": recent_deploys},
    {"name": "search_logs", "description": "Search log messages, optionally filtered by service.",
     "parameters": {"type": "object",
        "properties": {"query": {"type": "string"}, "service": {"type": "string"}},
        "required": ["query"]}, "fn": search_logs},
    {"name": "get_runbook", "description": "Fetch a runbook by name.",
     "parameters": {"type": "object",
        "properties": {"name": {"type": "string"}}, "required": ["name"]}, "fn": get_runbook},
]

def run_tool(name, args):
    for t in TOOLS:
        if t["name"] == name:
            # Return errors AS the tool result (don't crash the agent loop) so the
            # model can read the error and recover — e.g. retry with a fixed argument.
            try:
                return str(t["fn"](**args))
            except Exception as e:
                return f"error: tool '{name}' failed with args {args}: {e}"
    return f"error: unknown tool '{name}'"
