import sys
import os

# Make the repo root importable so "from src import tools" works when launched directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from src import tools

mcp = FastMCP("oncall-copilot")


@mcp.tool()
def list_services() -> str:
    "List known services."
    return tools.list_services()

@mcp.tool()
def get_metric(service: str, name: str) -> str:
    "Get recent values and trend for a service metric."
    return tools.get_metric(service, name)

@mcp.tool()
def recent_deploys(service: str) -> str:
    "List recent deploys for a service."
    return tools.recent_deploys(service)

@mcp.tool()
def search_logs(query: str, service: str = "") -> str:
    "Search log messages, optionally by service."
    return tools.search_logs(query, service or None)

@mcp.tool()
def get_runbook(name: str) -> str:
    "Fetch a runbook by name (e.g. 'checkout-5xx', 'db-latency')."
    return tools.get_runbook(name)


if __name__ == "__main__":
    mcp.run()
