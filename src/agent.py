from src import retriever, tools, config

SYSTEM_PROMPT = (
    "You are On-Call Copilot, an assistant for on-call engineers.\n"
    "- Use the provided runbook CONTEXT to answer, and cite the [source] you used.\n"
    "- If you need live data (metrics, logs, deploys), call a tool.\n"
    "- Never claim a service is healthy unless a metric confirms it.\n"
    "- You may PROPOSE remediation but must NOT execute destructive actions; "
    "say clearly that rollbacks/restarts need human approval.\n"
    "- If you cannot ground an answer in the context or tools, say you don't have enough information."
)


def answer(question, client):
    context = retriever.retrieve(question)                 # RAG step
    log = [{"type": "user",
            "text": f"Question: {question}\n\nCONTEXT:\n{context or '(none found)'}"}]

    for _ in range(config.MAX_AGENT_STEPS):
        resp = client.complete(log, system=SYSTEM_PROMPT, tools=tools.TOOLS)
        if resp["tool_calls"]:
            log.append({"type": "assistant_tools", "calls": resp["tool_calls"]})
            results = []
            for call in resp["tool_calls"]:
                out = tools.run_tool(call["name"], call["args"])
                print(f"   ↳ tool: {call['name']}({call['args']}) -> {out[:80]}...")
                results.append({"id": call["id"], "name": call["name"], "content": out})
            log.append({"type": "tool_results", "results": results})
            continue                                        # loop again with new evidence
        return resp["text"]                                 # no tool call = final answer
    return "Stopped after max steps without a grounded answer."
