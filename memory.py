"""Thin wrapper around the official Hindsight Python client (hindsight-client).

Only two Hindsight operations are used for the workflow:
  * retain(): store an interaction in the customer's memory bank
  * recall(): retrieve memories relevant to the customer's new message

Each customer gets their own memory bank: support-<customer-id>-<run-id>.
Nothing here is cached or faked; if Hindsight fails, the error is returned to the UI.
"""
import os
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RecallOutcome:
    ok: bool
    memories: list = field(default_factory=list)  # [{"text", "type", "when"}]
    error: str = ""


@dataclass
class RetainOutcome:
    ok: bool
    error: str = ""


class SupportMemory:
    def __init__(self, run_id: str):
        self.base_url = os.getenv("HINDSIGHT_BASE_URL", "http://localhost:8888").rstrip("/")
        self.api_key = os.getenv("HINDSIGHT_API_KEY") or None
        self.run_id = run_id
        self._client = None
        self.init_error = ""
        self._banks_ready = set()
        try:
            from hindsight_client import Hindsight

            kwargs = {"base_url": self.base_url}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            self._client = Hindsight(**kwargs)
        except Exception as e:  # missing package or bad config
            self.init_error = f"Could not create Hindsight client: {e}"

    def bank_id(self, customer_id: str) -> str:
        return f"support-{customer_id.lower()}-{self.run_id}"

    def health(self) -> tuple[bool, str]:
        if self._client is None:
            return False, self.init_error
        try:
            with urllib.request.urlopen(f"{self.base_url}/health", timeout=4) as r:
                return (r.status == 200), f"HTTP {r.status} from {self.base_url}"
        except Exception as e:
            return False, f"Hindsight not reachable at {self.base_url}: {e}"

    def _ensure_bank(self, bank_id: str, customer_name: str):
        if bank_id in self._banks_ready:
            return
        try:
            self._client.create_bank(bank_id=bank_id, name=f"Support memory: {customer_name}")
        except Exception:
            pass  # already exists, or retain() will create it on first write
        self._banks_ready.add(bank_id)

    def retain(self, customer_id, customer_name, content, when: datetime, context="customer support interaction") -> RetainOutcome:
        if self._client is None:
            return RetainOutcome(False, self.init_error)
        bank = self.bank_id(customer_id)
        try:
            self._ensure_bank(bank, customer_name)
            self._client.retain(bank_id=bank, content=content, context=context, timestamp=when)
            return RetainOutcome(True)
        except Exception as e:
            return RetainOutcome(False, f"Hindsight retain failed: {e}")

    def recall(self, customer_id, query, max_results=6) -> RecallOutcome:
        if self._client is None:
            return RecallOutcome(False, error=self.init_error)
        try:
            resp = self._client.recall(bank_id=self.bank_id(customer_id), query=query, budget="mid", max_tokens=1500)
            results = getattr(resp, "results", resp) or []
            out = []
            for r in list(results)[:max_results]:
                when = getattr(r, "occurred_start", None) or getattr(r, "mentioned_at", None)
                out.append({
                    "text": getattr(r, "text", str(r)),
                    "type": getattr(r, "type", None) or "memory",
                    "when": str(when)[:16] if when else "",
                })
            return RecallOutcome(True, out)
        except Exception as e:
            return RecallOutcome(False, error=f"Hindsight recall failed: {e}")


def format_memory_block(memories: list) -> str:
    """Turn recalled memories into the text block that is given to the LLM."""
    lines = []
    for m in memories:
        stamp = f" [{m['when']}]" if m["when"] else ""
        lines.append(f"-{stamp} {m['text']}")
    return "\n".join(lines)


def build_retain_content(customer, customer_id, message, reply, when: datetime) -> str:
    return (
        f"Support chat on {when:%Y-%m-%d %H:%M}. Customer {customer['name']} (ID {customer_id}, "
        f"platform: {customer['platform']}) wrote: \"{message}\" "
        f"The support agent replied: \"{reply}\""
    )
