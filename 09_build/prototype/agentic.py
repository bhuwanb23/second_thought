"""
agentic.py — job 2 of the AI: an agent that can propose, but not move money.

The agent may read freely and may *propose* money actions. A money action only
executes with an approval token bound to the exact tool and the exact arguments,
so nothing can be swapped between approval and execution.

Extraction lives in extraction.py and is re-exported here, so callers have one
import surface.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass, field
from datetime import date, timedelta

from extraction import (  # noqa: F401  (re-exported)
    EXTRACTION_SCHEMA, EXTRACTION_SYSTEM, MAX_OBLIGATIONS, Draft, Extraction,
    _extract_with_mock, extract, rule_extract, validate_extraction,
)
from llm import ChatModel, MockChat, Reply, ToolCall

MAX_APPROVAL_STEPS = 8
APPROVAL_SECRET = os.environ.get("APPROVAL_SECRET", "dev-only-change-me").encode()


def approval_secret_source() -> str:
    """'env' when the HMAC secret came from the environment, else 'default'."""
    return "env" if os.environ.get("APPROVAL_SECRET") else "default"


# ==========================================================================
# 2. APPROVAL TOKENS
# ==========================================================================
def _canonical(tool: str, args: dict) -> bytes:
    return json.dumps({"tool": tool, "args": args}, sort_keys=True,
                      separators=(",", ":")).encode()


def make_approval_token(tool: str, args: dict) -> str:
    """A token is bound to the exact tool AND the exact arguments."""
    return hmac.new(APPROVAL_SECRET, _canonical(tool, args), hashlib.sha256).hexdigest()[:32]


def check_approval_token(tool: str, args: dict, token: str | None) -> bool:
    if not token:
        return False
    return hmac.compare_digest(token, make_approval_token(tool, args))


# ==========================================================================
# 3. THE AGENT LOOP
# ==========================================================================
@dataclass
class ToolResult:
    name: str
    status: str
    data: dict = field(default_factory=dict)


class Toolbox:
    """
    The agent's tool surface.

    Read tools run freely. Money tools return `approval_required` with a
    proposal and a token — they never execute on the model's word alone.
    """

    MONEY_TOOLS = {"create_scheduled_invoice", "authorize_payment"}

    def __init__(self, paypal_client, decision_fn, ledger=None):
        self.client = paypal_client
        self.decision_fn = decision_fn
        self.ledger = ledger

    # -- schemas offered to the model -------------------------------------
    def schemas(self) -> list[dict]:
        def fn(name, desc, props, required):
            return {"type": "function", "function": {
                "name": name, "description": desc,
                "parameters": {"type": "object", "properties": props,
                               "required": required}}}

        return [
            fn("extract_obligations",
               "Record the shopper's stated bills and income.",
               {"obligations": {"type": "array", "items": {"type": "object"}}},
               ["obligations"]),
            fn("decide_purchase",
               "Run the deterministic affordability engine for an amount.",
               {"amount_minor": {"type": "integer"}}, ["amount_minor"]),
            fn("create_scheduled_invoice",
               "ISSUE A REAL PAYPAL INVOICE due on a date. Requires human approval.",
               {"amount_minor": {"type": "integer"}, "due_date": {"type": "string"}},
               ["amount_minor", "due_date"]),
            fn("authorize_payment",
               "PLACE A PAYPAL AUTHORIZATION HOLD. Requires human approval.",
               {"amount_minor": {"type": "integer"}}, ["amount_minor"]),
        ]

    # -- execution ---------------------------------------------------------
    def call(self, name: str, args: dict, approval_token: str | None = None) -> ToolResult:
        if name in self.MONEY_TOOLS:
            if not check_approval_token(name, args, approval_token):
                return ToolResult(name, "approval_required",
                                  {"proposal": args,
                                   "required_token": make_approval_token(name, args),
                                   "hint": "call with the token returned by /api/approve"})
            return self._execute_money(name, args)

        if name == "decide_purchase":
            amount = args.get("amount_minor")
            if not isinstance(amount, int) or amount <= 0:
                return ToolResult(name, "error", {"error": "amount_minor must be a positive int"})
            return ToolResult(name, "ok", self.decision_fn(amount))

        if name == "extract_obligations":
            return ToolResult(name, "ok", {"recorded": len(args.get("obligations") or [])})

        return ToolResult(name, "error", {"error": f"unknown tool {name}"})

    def _execute_money(self, name: str, args: dict) -> ToolResult:
        if name == "create_scheduled_invoice":
            due = args.get("due_date")
            amount = args.get("amount_minor")
            if not isinstance(amount, int) or amount <= 0:
                return ToolResult(name, "error", {"error": "bad amount"})
            try:
                date.fromisoformat(str(due))
            except ValueError:
                return ToolResult(name, "error", {"error": "bad due_date"})
            inv = self.client.create_invoice(amount, str(due),
                                             note="Scheduled to your payday.")
            return ToolResult(name, "executed", {"invoice_id": inv.get("id"), "due": due})
        if name == "authorize_payment":
            amount = args.get("amount_minor")
            if not isinstance(amount, int) or amount <= 0:
                return ToolResult(name, "error", {"error": "bad amount"})
            order = self.client.create_order(amount, intent="AUTHORIZE",
                                             reference="AGENT-APPROVED")
            auth = self.client.authorize_order(order["id"])
            auth_id = auth["purchase_units"][0]["payments"]["authorizations"][0]["id"]
            return ToolResult(name, "executed", {"order_id": order["id"],
                                                 "authorization_id": auth_id})
        return ToolResult(name, "error", {"error": "unknown money tool"})


@dataclass
class AgentRun:
    steps: list[dict] = field(default_factory=list)
    final: str = ""
    pending_approval: dict | None = None
    engine: str = "rules"

    def to_dict(self) -> dict:
        return {"steps": self.steps, "final": self.final,
                "pending_approval": self.pending_approval, "engine": self.engine}


AGENT_SYSTEM = (
    "You are the Second Thought agent. You help a shopper decide whether a purchase "
    "fits their month, using a deterministic engine as the source of truth. "
    "Never state a verdict or an amount the engine did not produce. "
    "If the shopper should defer, propose create_scheduled_invoice. "
    "Money tools require human approval and will tell you so; do not retry them."
)


def run_agent(model: ChatModel, toolbox: Toolbox, goal: str,
              approval_token: str | None = None,
              max_steps: int = MAX_APPROVAL_STEPS) -> AgentRun:
    """A bounded tool-calling loop. Stops on a final answer or a pending approval."""
    run = AgentRun(engine=getattr(model, "name", "rules"))
    messages: list[dict] = [{"role": "system", "content": AGENT_SYSTEM},
                            {"role": "user", "content": goal}]
    tools = toolbox.schemas()

    for _ in range(max_steps):
        reply = model.complete(messages, tools=tools)
        if not reply.is_tool_call:
            run.final = reply.content
            return run

        call: ToolCall = reply.tool_calls[0]
        messages.append({"role": "assistant", "content": reply.content or "",
                         "tool_calls": [{"id": call.id, "type": "function",
                                         "function": {"name": call.name,
                                                      "arguments": json.dumps(call.arguments)}}]})
        result = toolbox.call(call.name, call.arguments, approval_token)
        run.steps.append({"tool": call.name, "status": result.status,
                          "data": result.data})
        messages.append({"role": "tool", "tool_call_id": call.id,
                         "content": json.dumps(result.data, default=str)})

        if result.status == "approval_required":
            run.pending_approval = {"tool": call.name, "args": call.arguments,
                                    "token": result.data.get("required_token")}
            return run
        if result.status == "executed":
            run.final = f"{call.name} executed"
            return run

    run.final = "stopped: step limit reached"
    return run
