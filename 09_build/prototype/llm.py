"""
llm.py — the model interface.

Three implementations behind one interface:

  OpenAIChat   real tool-calling against any OpenAI-compatible endpoint
  MockChat     a scripted model so the agentic path can be exercised, recorded
               and tested with no key and no network. Always labelled "mock".
  None         triggers the deterministic rule-based path

Nothing here decides anything about money. See agentic.py for the approval gate.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    name: str
    arguments: dict
    id: str = "call_0"


@dataclass
class Reply:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    @property
    def is_tool_call(self) -> bool:
        return bool(self.tool_calls)


class ChatModel:
    name = "none"

    def complete(self, messages: list[dict], tools: list[dict] | None = None,
                 temperature: float = 0) -> Reply:
        raise NotImplementedError

    def available(self) -> bool:
        return False


class OpenAIChat(ChatModel):
    """Any OpenAI-compatible /chat/completions endpoint with tool calling."""

    name = "openai"

    def __init__(self, model: str | None = None, base_url: str | None = None,
                 api_key: str | None = None, timeout: int = 30):
        self.model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL")
                         or "https://api.openai.com/v1").rstrip("/")
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        self.timeout = timeout

    def available(self) -> bool:
        return bool(self.api_key)

    def complete(self, messages, tools=None, temperature=0) -> Reply:
        payload: dict = {"model": self.model, "messages": messages,
                         "temperature": temperature}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.api_key}"},
            method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            body = json.loads(resp.read().decode())
        msg = body["choices"][0]["message"]
        calls = []
        for c in msg.get("tool_calls") or []:
            fn = c.get("function", {})
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            calls.append(ToolCall(name=fn.get("name", ""), arguments=args,
                                  id=c.get("id", "call_0")))
        return Reply(content=msg.get("content") or "", tool_calls=calls, raw=body)


class MockChat(ChatModel):
    """
    A scripted model.

    It exists so the tool-calling path is real code that runs, is tested, and can
    be recorded on screen without a key. It is never presented as a real model:
    every payload it produces is tagged engine="llm-mock" and the UI badge says
    MOCK. Replacing it with OpenAIChat is one environment variable.
    """

    name = "mock"

    def __init__(self, script: list[Reply] | None = None):
        self.script = list(script or [])
        self.calls: list[dict] = []

    def available(self) -> bool:
        return True

    def complete(self, messages, tools=None, temperature=0) -> Reply:
        self.calls.append({"messages": messages, "tools": [t.get("function", {}).get("name")
                                                           for t in (tools or [])]})
        if self.script:
            return self.script.pop(0)
        return Reply(content="I've done what I can without calling a tool.")

    # -- helpers for building scripts in tests and demos ----------------
    @staticmethod
    def extract_script(text_obligations: list[dict]) -> Reply:
        return Reply(tool_calls=[ToolCall(
            name="extract_obligations",
            arguments={"obligations": text_obligations})])

    @staticmethod
    def decide_script(amount_minor: int) -> Reply:
        return Reply(tool_calls=[ToolCall(name="decide_purchase",
                                          arguments={"amount_minor": amount_minor})])

    @staticmethod
    def invoice_script(due_date: str, amount_minor: int) -> Reply:
        return Reply(tool_calls=[ToolCall(
            name="create_scheduled_invoice",
            arguments={"amount_minor": amount_minor, "due_date": due_date})])


def model_from_env(force_mock: bool = False) -> ChatModel:
    if force_mock:
        return MockChat()
    m = OpenAIChat()
    return m if m.available() else MockChat()


def describe(model: ChatModel) -> dict:
    """What the UI and the submission's 'Tools used' field should say."""
    if model.name == "openai":
        return {"engine": "llm", "model": getattr(model, "model", "?"),
                "live": True, "note": "live tool-calling model"}
    if model.name == "mock":
        return {"engine": "llm-mock", "model": "scripted-mock", "live": False,
                "note": "scripted stand-in — the same code path, no network"}
    return {"engine": "rules", "model": "none", "live": False,
            "note": "deterministic extraction"}
