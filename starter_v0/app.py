"""Streamlit UI for the Research Agent.

Run from starter_v0/:
    streamlit run app.py

Tab "Chat": chat with the agent using any saved version (artifacts/versions/vN/).
Tab "So sánh version": scores of every version from runs/*.json, and which eval
cases got fixed / broken between two versions.

Reuses the multi-round tool loop from chat.py, so the UI behaves exactly like
`python chat.py` and also writes transcripts/*.transcript.json.
"""
from __future__ import annotations

import csv
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
VERSIONS_DIR = ARTIFACTS_DIR / "versions"
RUNS_DIR = ROOT / "runs"
VERSION_LOG = ARTIFACTS_DIR / "version_log.csv"

SAMPLE_QUESTIONS = [
    "Tweet mới nhất của Sam Altman là gì?",
    "Tin tức AI hôm nay có gì nổi bật?",
    "Hacker News đang bàn gì về Rust?",
    "Retrieval-Augmented Generation là gì?",
    "Tóm tắt 5 tweet mới nhất giúp mình",
    "Đăng bản tin này lên Telegram giúp mình",
]

st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="wide")


# ---------------- Helpers ----------------
def available_versions() -> dict[str, tuple[Path, Path]]:
    """{label: (system_prompt_path, tools_path)} — saved versions + the live artifacts."""
    versions: dict[str, tuple[Path, Path]] = {}
    if VERSIONS_DIR.exists():
        for folder in sorted(p for p in VERSIONS_DIR.iterdir() if p.is_dir()):
            prompt, tools = folder / "system_prompt.md", folder / "tools.yaml"
            if prompt.exists() and tools.exists():
                versions[folder.name] = (prompt, tools)
    versions["current (artifacts/)"] = (ARTIFACTS_DIR / "system_prompt.md", ARTIFACTS_DIR / "tools.yaml")
    return versions


def load_version_log() -> dict[str, dict[str, str]]:
    if not VERSION_LOG.exists():
        return {}
    with VERSION_LOG.open(encoding="utf-8") as handle:
        return {row["version"]: row for row in csv.DictReader(handle) if row.get("version")}


def load_runs() -> list[dict[str, Any]]:
    runs = []
    for path in sorted(RUNS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        data["_file"] = path.name
        runs.append(data)
    return runs


def latest_run_per_version(runs: list[dict[str, Any]], suite: str) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for run in runs:
        if run.get("suite") != suite:
            continue
        version = str(run.get("version"))
        if version not in latest or run.get("generated_at", "") > latest[version].get("generated_at", ""):
            latest[version] = run
    return dict(sorted(latest.items()))


def case_status(run: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in run.get("results", [])}


def render_events(events: list[dict[str, Any]]) -> None:
    for event in events:
        args = json.dumps(event.get("args", {}), ensure_ascii=False)
        with st.expander(f"🔧 {event.get('tool')}({args})", expanded=False):
            st.json(event.get("result", {}))


# ---------------- Sidebar ----------------
versions = available_versions()
version_names = list(versions)
default_index = max(0, len(version_names) - 2)  # newest saved version

with st.sidebar:
    st.header("⚙️ Cài đặt")
    version = st.selectbox("Version của agent", version_names, index=default_index,
                           help="Mỗi version = một bộ system_prompt.md + tools.yaml trong artifacts/versions/")
    provider_name = st.selectbox("Provider", PROVIDERS, index=0)
    model = st.text_input("Model", value=DEFAULT_MODEL)
    show_tools = st.toggle("Hiện chi tiết tool call", value=True)
    history_window = st.slider("Số lượt nhớ (history window)", 0, 10, 5)
    max_rounds = st.slider("Số vòng tool tối đa", 1, 6, 4)
    if st.button("🗑️ Cuộc trò chuyện mới", use_container_width=True):
        for key in ("messages", "history", "transcript", "transcript_path", "chat_version"):
            st.session_state.pop(key, None)
        st.rerun()

    st.divider()
    st.caption("Câu hỏi mẫu")
    for question in SAMPLE_QUESTIONS:
        if st.button(question, use_container_width=True, key=f"sample_{question}"):
            st.session_state["pending_input"] = question


# ---------------- Load the selected version ----------------
system_prompt_path, tools_path = versions[version]
version_label = version.split(" ")[0]
system_prompt = system_prompt_path.read_text(encoding="utf-8")
declarations = load_tool_declarations(tools_path)
openai_tools = to_openai_tools(declarations)
artifact_version = build_artifact_version(version_label, system_prompt_path, tools_path)

# Switching version starts a fresh conversation (each transcript = one version).
if st.session_state.get("chat_version") != version:
    for key in ("messages", "history", "transcript", "transcript_path"):
        st.session_state.pop(key, None)
    st.session_state.chat_version = version

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.history = []
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(version_label), "ui", safe_slug(provider_name), timestamp])
    st.session_state.transcript_path = ROOT / "transcripts" / f"{transcript_id}.transcript.json"
    st.session_state.transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": model,
        "source": "streamlit_ui",
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }


# ---------------- Header ----------------
st.title("🔎 Research Agent")
log_row = load_version_log().get(version_label, {})
st.caption(
    f"**Version: `{version_label}`** · Artifact: `{artifact_version.artifact_version}` · "
    f"Provider: `{provider_name}` · Model: `{model}`"
)
if log_row:
    st.info(f"**{version_label}** — {log_row.get('reason', '')}  \n"
            f"Điểm eval base: {log_row.get('metric_before', '-')} → **{log_row.get('metric_after', '-')}**")

tab_chat, tab_compare, tab_prompt = st.tabs(["💬 Chat", "📊 So sánh version", "📝 Prompt & tools của version này"])


# ---------------- Tab: Chat ----------------
with tab_chat:
    st.caption(f"{len(declarations)} tools: " + ", ".join(f"`{d['name']}`" for d in declarations))
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if show_tools and message.get("events"):
                render_events(message["events"])

user_text = st.chat_input(f"Hỏi agent ({version_label})… ví dụ: Tin AI hôm nay có gì?")
if not user_text and st.session_state.get("pending_input"):
    user_text = st.session_state.pop("pending_input")

if user_text:
    with tab_chat:
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
                    result = run_model_tool_loop(
                        provider=make_provider(provider_name),
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
                except Exception as exc:  # show provider errors instead of crashing
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


# ---------------- Tab: Compare versions ----------------
with tab_compare:
    runs = load_runs()
    suite = st.radio("Bộ eval", ["base", "group"], horizontal=True,
                     format_func=lambda s: "Base (20 case của đề)" if s == "base" else "Group (10 case của nhóm)")
    per_version = latest_run_per_version(runs, suite)

    if not per_version:
        st.warning(f"Chưa có run nào cho suite `{suite}` trong runs/. Chạy run_eval.py trước.")
    else:
        version_log = load_version_log()
        rows = []
        for name, run in per_version.items():
            summary = run.get("summary", {})
            rows.append({
                "version": name,
                "case_accuracy": summary.get("case_accuracy"),
                "passed": f"{summary.get('passed_cases')}/{summary.get('total_cases')}",
                "routing": summary.get("tool_routing_accuracy"),
                "args": summary.get("argument_accuracy"),
                "multiturn": summary.get("multiturn_accuracy"),
                "thay đổi": version_log.get(name, {}).get("reason", ""),
                "run_file": run["_file"],
            })
        st.subheader("Điểm từng version (run mới nhất của mỗi version)")
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.bar_chart({row["version"]: row["case_accuracy"] or 0 for row in rows})

        names = list(per_version)
        if len(names) >= 2:
            st.subheader("Version sau hơn version trước ở điểm nào?")
            col_a, col_b = st.columns(2)
            old = col_a.selectbox("Version cũ", names, index=len(names) - 2)
            new = col_b.selectbox("Version mới", names, index=len(names) - 1)
            old_cases, new_cases = case_status(per_version[old]), case_status(per_version[new])

            fixed, broken, still_fail = [], [], []
            for case_id, new_item in new_cases.items():
                was = old_cases.get(case_id, {}).get("result", {}).get("passed")
                now = new_item["result"]["passed"]
                what = new_item.get("metadata", {}).get("what_it_tests", "")
                if now and was is False:
                    fixed.append((case_id, what))
                elif not now and was:
                    broken.append((case_id, what, new_item["result"].get("failures", [])))
                elif not now:
                    still_fail.append((case_id, what, new_item["result"].get("failures", [])))

            c1, c2, c3 = st.columns(3)
            c1.metric("✅ Được sửa", len(fixed))
            c2.metric("❌ Bị hỏng thêm", len(broken))
            c3.metric("⏳ Vẫn FAIL", len(still_fail))
            if fixed:
                st.markdown("**✅ Case được sửa ở " + new + "**")
                for case_id, what in fixed:
                    st.markdown(f"- `{case_id}` — {what}")
            if broken:
                st.markdown("**❌ Case bị hỏng ở " + new + "**")
                for case_id, what, failures in broken:
                    st.markdown(f"- `{case_id}` — {what}  \n  ↳ {'; '.join(failures)}")
            if still_fail:
                with st.expander(f"⏳ {len(still_fail)} case vẫn FAIL"):
                    for case_id, what, failures in still_fail:
                        st.markdown(f"- `{case_id}` — {what}  \n  ↳ {'; '.join(failures)}")

        with st.expander("Bảng PASS/FAIL từng case qua các version"):
            all_ids = list(dict.fromkeys(cid for run in per_version.values() for cid in case_status(run)))
            matrix = []
            for cid in all_ids:
                row = {"case": cid}
                for name, run in per_version.items():
                    item = case_status(run).get(cid)
                    row[name] = "—" if item is None else ("✅" if item["result"]["passed"] else "❌")
                matrix.append(row)
            st.dataframe(matrix, use_container_width=True, hide_index=True)


# ---------------- Tab: Prompt & tools ----------------
with tab_prompt:
    st.caption(f"`{system_prompt_path.relative_to(ROOT)}` · `{tools_path.relative_to(ROOT)}`")
    st.subheader("System prompt")
    st.code(system_prompt, language="markdown")
    st.subheader("Tools")
    st.dataframe([{"name": d["name"], "description": d.get("description", "")} for d in declarations],
                 use_container_width=True, hide_index=True)