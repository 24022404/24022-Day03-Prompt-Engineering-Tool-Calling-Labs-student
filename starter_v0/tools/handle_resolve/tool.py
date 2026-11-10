from __future__ import annotations

from typing import Any

from tools._shared import err, fold_text

# folded name -> handle (no "@")
KNOWN_HANDLES: dict[str, str] = {
    "sam altman": "sama",
    "elon musk": "elonmusk",
    "andrej karpathy": "karpathy",
    "yann lecun": "ylecun",
    "andrew ng": "AndrewYNg",
    "demis hassabis": "demishassabis",
    "satya nadella": "satyanadella",
    "sundar pichai": "sundarpichai",
    "jensen huang": "nvidia",
    "dario amodei": "DarioAmodei",
    "greg brockman": "gdb",
    "fei-fei li": "drfeifei",
    "openai": "OpenAI",
    "anthropic": "AnthropicAI",
    "google deepmind": "GoogleDeepMind",
    "deepmind": "GoogleDeepMind",
    "nvidia": "nvidia",
    "hugging face": "huggingface",
    "huggingface": "huggingface",
    "meta ai": "AIatMeta",
    "mistral": "MistralAI",
    "xai": "xai",
}


def resolve_handle(name: str = "") -> dict[str, Any]:
    try:
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        raw = name.strip()
        if not raw:
            return {"tool": "handle_resolve", "name": name, "handle": None, "found": False, "candidates": []}

        # Already a handle like "@sama" -> strip the "@".
        if raw.startswith("@"):
            return {"tool": "handle_resolve", "name": name, "handle": raw.lstrip("@"), "found": True, "candidates": []}

        key = " ".join(fold_text(raw).split())
        if key in KNOWN_HANDLES:
            return {"tool": "handle_resolve", "name": name, "handle": KNOWN_HANDLES[key], "found": True, "candidates": []}

        # Partial match (e.g. "Altman", "Karpathy") -> suggest candidates, do not guess.
        candidates = [handle for known, handle in KNOWN_HANDLES.items() if key in known or known in key]
        if len(candidates) == 1:
            return {"tool": "handle_resolve", "name": name, "handle": candidates[0], "found": True, "candidates": []}
        return {"tool": "handle_resolve", "name": name, "handle": None, "found": False, "candidates": sorted(set(candidates))}
    except Exception as exc:
        return err("handle_resolve", exc)