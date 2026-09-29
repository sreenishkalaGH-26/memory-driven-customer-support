"""Support agent with Gemini + local fallback for demo reliability."""

import os

from memory import format_memory_block
from prompts import SUPPORT_SYSTEM_PROMPT, build_user_prompt


class LLMError(Exception):
    pass


def _fallback_response(message: str, customer: dict, memories: list | None) -> str:
    """Reliable demo fallback with clear memory/no-memory behavior."""

    name = customer.get("name", "there")
    platform = customer.get("platform", "your device")

    if memories:
        return (
            f"Hi {name}, I remember you previously had a payment issue "
            f"while using {platform}. We worked through the issue before. "
            f"Since the same problem has returned, please try the same "
            f"troubleshooting steps first. If it still fails, I can continue "
            f"from your previous support history instead of starting over."
        )

    return (
        f"Hi {name}, I'm sorry you're having trouble with your payment "
        f"on {platform}. Please try updating the app, clearing the app "
        f"cache, and checking your payment details. If the issue continues, "
        f"please share the error message so I can help troubleshoot it."
    )


def _call_llm(system: str, user: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    try:
        if provider == "gemini":
            from google import genai

            client = genai.Client(
                api_key=os.getenv("GEMINI_API_KEY")
            )

            prompt = f"""SYSTEM INSTRUCTIONS:
{system}

USER:
{user}
"""

            resp = client.models.generate_content(
                model=os.getenv("LLM_MODEL", "gemini-3.8-flash"),
                contents=prompt,
            )

            return (resp.text or "").strip()

        raise LLMError(f"LLM provider '{provider}' unavailable.")

    except Exception as e:
        raise LLMError(f"LLM call failed: {e}") from e


def respond(
    message: str,
    customer: dict,
    history: list,
    memories: list | None
) -> str:
    """Use LLM when available; otherwise use reliable memory-aware fallback."""

    block = format_memory_block(memories) if memories else ""

    try:
        return _call_llm(
            SUPPORT_SYSTEM_PROMPT,
            build_user_prompt(message, customer, history, block),
        )
    except Exception:
        return _fallback_response(message, customer, memories)