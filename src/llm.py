"""Thin LiteLLM wrapper so every LLM call goes through one place.

Cost-aware routing (the Mercanis 'LiteLLM' bullet): heavy reasoning (planner,
ReAct) uses the strong model; cheap structured extraction uses the small one.
Set the model strings to whatever your provider supports, and export the key:
    export ANTHROPIC_API_KEY=...      # or OPENAI_API_KEY, etc.

LiteLLM model-string examples: "anthropic/claude-sonnet-4-5",
"anthropic/claude-haiku-4-5", "openai/gpt-4o-mini". Adjust to your account.
"""
from __future__ import annotations

import json
import os

import litellm

PLANNER_MODEL = os.getenv("PLANNER_MODEL", "anthropic/claude-sonnet-4-5")
EXTRACTOR_MODEL = os.getenv("EXTRACTOR_MODEL", "anthropic/claude-haiku-4-5")


def llm(prompt: str, *, system: str = "", heavy: bool = True,
        temperature: float = 0.2) -> str:
    """Single completion. heavy=True → planner model, False → cheap extractor."""
    model = PLANNER_MODEL if heavy else EXTRACTOR_MODEL
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = litellm.completion(model=model, messages=messages,
                              temperature=temperature, max_tokens=1500)
    return resp["choices"][0]["message"]["content"]


def llm_json(prompt: str, *, system: str = "", heavy: bool = False) -> dict:
    """Same as llm() but parses a JSON object out of the reply (tolerates fences)."""
    text = llm(prompt, system=system + " Reply with ONLY a JSON object, no prose.",
               heavy=heavy)
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)
