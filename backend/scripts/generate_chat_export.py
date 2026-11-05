"""
Chat Exporter Script for Whicoustic Project
Reads conversation transcript logs and produces a comprehensive Markdown export.
"""

import json
import re
from pathlib import Path
from datetime import datetime

TRANSCRIPT_PATH = Path(r"C:\Users\ritsa\.gemini\antigravity-ide\brain\8d229fa8-7a5a-4939-9e3f-90ce3a32aa08\.system_generated\logs\transcript_full.jsonl")
if not TRANSCRIPT_PATH.exists():
    TRANSCRIPT_PATH = Path(r"C:\Users\ritsa\.gemini\antigravity-ide\brain\8d229fa8-7a5a-4939-9e3f-90ce3a32aa08\.system_generated\logs\transcript.jsonl")

OUTPUT_MD_WORKSPACE = Path(r"D:\Main\docs\CHAT_EXPORT.md")
OUTPUT_MD_ARTIFACT = Path(r"C:\Users\ritsa\.gemini\antigravity-ide\brain\8d229fa8-7a5a-4939-9e3f-90ce3a32aa08\chat_export.md")


def clean_user_text(raw_text: str) -> str:
    m = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", raw_text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return raw_text.split("<ADDITIONAL_METADATA>")[0].strip()


def export_chat():
    turns = []
    current_turn = None

    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue

            etype = entry.get("type")
            source = entry.get("source")
            content = entry.get("content") or ""

            if etype == "USER_INPUT" and source == "USER_EXPLICIT":
                if current_turn:
                    turns.append(current_turn)
                current_turn = {
                    "turn_index": len(turns) + 1,
                    "user": clean_user_text(content),
                    "actions": [],
                    "responses": [],
                    "start_line": line_idx,
                }
            elif current_turn is not None:
                if etype == "PLANNER_RESPONSE":
                    tool_calls = entry.get("tool_calls") or []
                    for tc in tool_calls:
                        args = tc.get("args") or tc.get("function", {}).get("arguments") or {}
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except Exception:
                                args = {}
                        summary = args.get("toolSummary") or tc.get("name") or "Action"
                        if summary and summary not in current_turn["actions"]:
                            current_turn["actions"].append(summary)

                    if content.strip():
                        # Exclude intermediate progress notifications if final is present
                        current_turn["responses"].append(content.strip())

                elif etype in (
                    "RUN_COMMAND",
                    "VIEW_FILE",
                    "CODE_ACTION",
                    "LIST_DIRECTORY",
                    "GREP_SEARCH",
                    "BROWSER_SUBAGENT",
                ):
                    tool_summary = entry.get("toolSummary")
                    if tool_summary and tool_summary not in current_turn["actions"]:
                        current_turn["actions"].append(tool_summary)

    if current_turn:
        turns.append(current_turn)

    # Build Markdown
    lines = []
    lines.append("# Whicoustic Project: Full Pair-Programming Chat Transcript Export")
    lines.append("")
    lines.append("> **Workspace**: `D:\\Main`  ")
    lines.append("> **Session ID**: `8d229fa8-7a5a-4939-9e3f-90ce3a32aa08`  ")
    lines.append(f"> **Export Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append("> **Total Conversation Turns**: " + str(len(turns)) + "  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Table of Conversation Turns")
    lines.append("")
    for t in turns:
        u_summary = t["user"].replace("\n", " ")
        if len(u_summary) > 75:
            u_summary = u_summary[:72] + "..."
        lines.append(f"- [Turn {t['turn_index']}: {u_summary}](#turn-{t['turn_index']})")
    lines.append("")
    lines.append("---")
    lines.append("")

    for t in turns:
        lines.append(f"## Turn {t['turn_index']}")
        lines.append("")
        lines.append("### 👤 User")
        lines.append(f"```text\n{t['user']}\n```")
        lines.append("")

        if t["actions"]:
            lines.append("### 🛠️ Actions Executed")
            for act in t["actions"][:12]:
                lines.append(f"- {act}")
            if len(t["actions"]) > 12:
                lines.append(f"- *...and {len(t['actions']) - 12} additional actions*")
            lines.append("")

        lines.append("### 🤖 Assistant Response")
        if t["responses"]:
            # Present the most complete / final response for this turn
            final_resp = t["responses"][-1]
            lines.append(final_resp)
        else:
            lines.append("*(No text response recorded)*")
        lines.append("")
        lines.append("---")
        lines.append("")

    content_str = "\n".join(lines)

    OUTPUT_MD_WORKSPACE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_MD_WORKSPACE, "w", encoding="utf-8") as f:
        f.write(content_str)

    OUTPUT_MD_ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_MD_ARTIFACT, "w", encoding="utf-8") as f:
        f.write(content_str)

    print(f"Chat export successfully written to:\n1. {OUTPUT_MD_WORKSPACE}\n2. {OUTPUT_MD_ARTIFACT}")
    print(f"Total size: {len(content_str)} characters across {len(turns)} turns.")


if __name__ == "__main__":
    export_chat()
