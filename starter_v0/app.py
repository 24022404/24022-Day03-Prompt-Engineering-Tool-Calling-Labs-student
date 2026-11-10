"""Streamlit UI for the Research Agent.

Run from starter_v0/:
    streamlit run app.py

Reuses the multi-round tool loop from chat.py, so the UI behaves exactly like
`python chat.py` and also writes transcripts/*.transcript.json.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import (
    ARTIFACTS_DIR,
    ROOT,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

PROVIDERS = ["openrouter", "openai", "anthropic", "gemini", "ollama"]
DEFAULT_MODEL = os.getenv("UI_MODEL", "cx/gpt-6-luna")

SAMPLE_QUESTIONS = [
    "Tweet mới nhất của Sam Altman là gì?",
    "Tin tức AI hôm nay có gì nổi bật?",
    "Hacker News đang bàn gì về Rust?",
    "Transformer trong deep learning là gì?",
    "Tóm tắt 5 tweet mới nhất giúp mình",
    "Đăng bản tin này lên Telegram giúp mình",
]

st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="wide")


# ---------------- Sidebar: settings ----------------
with st.sidebar:
    st.header("⚙️ Cài đặt")
    provider_name = st.selectbox("Provider", PROVIDERS, index=0)
    model = st.text_input("Model", value=DEFAULT_MODEL)
    version = st.text_input("Version label", value="ui")
    show_tools = st.toggle("Hiện chi tiết tool call", value=True)
    history_window = st.slider("Số lượt nhớ (history window)", 0, 10, 5)
    max_rounds = st.slider("Số vòng tool tối đa", 1, 6, 4)
    if st.button("🗑️ Cuộc trò chuyện mới", use_container_width=True):
        for key in ("messages", "history", "transcript", "transcript_path"):
            st.session_state.pop(key, None)
        st.rerun()

    st.divider()
    st.caption("Câu hỏi mẫu")
    for question in SAMPLE_QUESTIONS:
        if st.button(question, use_container_width=True, key=f"sample_{question}"):
            st.session_state["pending_input"] = question


# ---------------- Load artifacts (re-read every run so prompt edits show up) ----------------
system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
tools_path = ARTIFACTS_DIR / "tools.yaml"
system_prompt = system_prompt_path.read_text(encoding="utf-8")
declarations = load_tool_declarations(tools_path)
openai_tools = to_openai_tools(declarations)
artifact_version = build_artifact_version(version, system_prompt_path, tools_path)


# ---------------- Session state ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []   # what the UI shows: {role, content, events}
    st.session_state.history = []    # what the model sees: {role, content}
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(version), "ui", safe_slug(provider_name), timestamp])
    st.session_state.transcript_path = ROOT / "transcripts" / f"{transcript_id}.transcript.json"
    st.session_state.transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": model,
        "source": "streamlit_ui",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }


def render_events(events: list[dict[str, Any]]) -> None:
    for event in events:
        tool = event.get("tool")
        args = json.dumps(event.get("args", {}), ensure_ascii=False)
        with st.expander(f"🔧 {tool}({args})", expanded=False):
            st.json(event.get("result", {}))


# ---------------- Header ----------------
st.title("🔎 Research Agent")
st.caption(
    f"Provider: `{provider_name}` · Model: `{model}` · Artifact: `{artifact_version.artifact_version}` · "
    f"{len(declarations)} tools: " + ", ".join(f"`{d['name']}`" for d in declarations)
)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if show_tools and message.get("events"):
            render_events(message["events"])


# ---------------- Chat input ----------------
user_text = st.chat_input("Hỏi agent… (ví dụ: Tin AI hôm nay có gì?)")
if not user_text and st.session_state.get("pending_input"):
    user_text = st.session_state.pop("pending_input")

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, history_window),
        {"role": "user", "content": user_text},
    ]
    turn_record: dict[str, Any] = {
        "turn_index": len(st.session_state.transcript["turns"]) + 1,
        "started_at": now_iso(),
        "user": user_text,
    }

    with st.chat_message("assistant"):
        with st.spinner("Agent đang suy nghĩ / gọi tool…"):
            try:
                provider = make_provider(provider_name)
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=model or None,
                    max_tool_rounds=max_rounds,
                )
                answer = result["assistant_text"] or "(không có nội dung)"
                if result["status"] == "waiting_for_user":
                    answer = f"❓ {answer}"
                events = result.get("tool_events", [])
                turn_record.update(result)
            except Exception as exc:  # show provider errors in the UI instead of crashing
                answer = f"⚠️ Lỗi provider: `{type(exc).__name__}: {exc}`"
                events = []
                turn_record.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})

        st.markdown(answer)
        if show_tools and events:
            render_events(events)

    st.session_state.messages.append({"role": "assistant", "content": answer, "events": events})
    st.session_state.history += [
        {"role": "user", "content": user_text},
        {"role": "assistant", "content": answer},
    ]

    turn_record["ended_at"] = now_iso()
    st.session_state.transcript["turns"].append(turn_record)
    write_transcript(Path(st.session_state.transcript_path), st.session_state.transcript)
