"""
Lightweight tool-calling loop: the model may invoke library tools before RAG answers.
Satisfies agentic AI requirement (reasoning + external tools) alongside RAG.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Union

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

BASE_DIR = Path(__file__).resolve().parent
MOVIES_FILE = BASE_DIR / "movies.txt"

_MAX_AGENT_TURNS = 4


@lru_cache(maxsize=1)
def _title_genre_rows() -> List[tuple[str, str]]:
    raw = MOVIES_FILE.read_text(encoding="utf-8")
    blocks = [b.strip() for b in raw.split("\n---\n") if b.strip()]
    rows: List[tuple[str, str]] = []
    for block in blocks:
        tm = re.search(r"^Title:\s*(.+)$", block, re.MULTILINE)
        gm = re.search(r"^Genre:\s*(.+)$", block, re.MULTILINE)
        title = tm.group(1).strip() if tm else "Unknown"
        genre = gm.group(1).strip() if gm else "Unknown"
        rows.append((title, genre))
    return rows


@tool
def library_movie_count() -> str:
    """Return how many films are in the curated library and a few example genres."""
    rows = _title_genre_rows()
    genres: set[str] = set()
    for _, g in rows:
        for part in g.split(","):
            part = part.strip()
            if part:
                genres.add(part)
    sample = ", ".join(sorted(genres)[:12])
    return (
        f"Total films in library: {len(rows)}. "
        f"Some genres present: {sample}. "
        f"(Use find_movies_by_genre for a filtered list.)"
    )


@tool
def find_movies_by_genre(genre_substring: str) -> str:
    """List up to 12 library titles whose Genre field contains genre_substring (case-insensitive)."""
    needle = (genre_substring or "").strip().lower()
    if not needle:
        return "Provide a non-empty genre substring (e.g. Sci-Fi, Comedy)."
    matches: List[str] = []
    for title, genre in _title_genre_rows():
        if needle in genre.lower():
            matches.append(title)
        if len(matches) >= 12:
            break
    if not matches:
        return f"No library films matched genre containing '{genre_substring}'."
    return "Matching titles: " + "; ".join(matches)


_TOOLS = [library_movie_count, find_movies_by_genre]
_TOOL_BY_NAME = {t.name: t for t in _TOOLS}


_AGENT_SYSTEM = """You are a library assistant for CineMindAI.
You may call tools to get real counts or title lists from the static movie library.
Rules:
- Call library_movie_count when the user asks how many films, size of the library, or what's available at a high level.
- Call find_movies_by_genre when they want examples by genre (e.g. sci-fi, comedy).
- If no tool is needed (pure opinion / plot question / comparison), respond with exactly: NONE
- If you used tools, reply with one short neutral paragraph (2–4 sentences) summarizing tool facts for the movie guide. No markdown headings."""


def _tool_call_as_dict(tc: Union[dict, Any]) -> Dict[str, Any]:
    if isinstance(tc, dict):
        return tc
    name = getattr(tc, "name", None)
    tid = getattr(tc, "id", None)
    args = getattr(tc, "args", None)
    if args is None and hasattr(tc, "get"):
        args = tc.get("args")
    if isinstance(args, str):
        args = {}
    return {"name": name, "id": tid, "args": args or {}}


def gather_tool_layer(api_key: str, user_question: str) -> str:
    """
    Optional LLM+tools pass. Returns text to append to the RAG query, or "".
    Never raises — returns "" on any failure.
    """
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=256,
            openai_api_key=api_key,
        ).bind_tools(_TOOLS)
        messages: List[Any] = [
            SystemMessage(content=_AGENT_SYSTEM),
            HumanMessage(content=user_question),
        ]
        turns = 0
        while turns < _MAX_AGENT_TURNS:
            turns += 1
            ai: AIMessage = llm.invoke(messages)
            messages.append(ai)
            calls = getattr(ai, "tool_calls", None) or []
            if not calls:
                text = (ai.content or "").strip()
                if not text or text.upper() == "NONE":
                    return ""
                return text
            for tc in calls:
                d = _tool_call_as_dict(tc)
                name = d.get("name")
                tid = d.get("id") or name or "tool"
                args: Dict[str, Any] = d.get("args") or {}
                if isinstance(args, str):
                    args = {}
                fn = _TOOL_BY_NAME.get(name or "")
                if fn is None:
                    out = f"Unknown tool: {name}"
                else:
                    try:
                        out = fn.invoke(args)
                    except Exception as e:
                        out = f"Tool error: {e}"
                messages.append(ToolMessage(content=str(out), tool_call_id=str(tid)))
        return ""
    except Exception:
        return ""
