"""OpenAI implementation of the neutral :class:`Provider` protocol.

v1 ships this provider only. It maps the neutral message/event types in
``base.py`` to and from the OpenAI Chat Completions streaming API.

Tool calling is forced single (``parallel_tool_calls=False``) so the
orchestrator can apply its one-tool-per-turn inline-confirmation model
without juggling partially-resolved tool batches.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from app.core.llm.base import (
    Done,
    LLMConfigError,
    ProviderEvent,
    ProviderMessage,
    Role,
    TextBlock,
    TextDelta,
    ToolResultBlock,
    ToolUse,
    ToolUseBlock,
    Usage,
)


def _extract_extra(*objs: Any) -> dict[str, Any] | None:
    for obj in objs:
        if obj is None:
            continue
        val = getattr(obj, "extra_content", None)
        if val:
            return val if isinstance(val, dict) else dict(val)
        model_extra = getattr(obj, "model_extra", None)
        if isinstance(model_extra, dict) and model_extra.get("extra_content"):
            extra = model_extra.get("extra_content")
            return extra if isinstance(extra, dict) else dict(extra)
        if isinstance(obj, dict) and obj.get("extra_content"):
            extra = obj.get("extra_content")
            return extra if isinstance(extra, dict) else dict(extra)
        raw_dict = getattr(obj, "__dict__", None)
        if isinstance(raw_dict, dict) and raw_dict.get("extra_content"):
            extra = raw_dict.get("extra_content")
            return extra if isinstance(extra, dict) else dict(extra)
    return None


class OpenAIProvider:
    """Streams completions from OpenAI / Gemini-compatible endpoint, speaking neutral types."""

    def __init__(self, *, api_key: str, base_url: str | None = None) -> None:
        if not api_key:
            raise LLMConfigError("LLM provider requires an API key")
        self._api_key = api_key
        base = (base_url or "https://api.openai.com/v1").rstrip("/")
        if not base.endswith("/chat/completions"):
            self._endpoint = f"{base}/chat/completions"
        else:
            self._endpoint = base

    async def complete(
        self,
        *,
        system: str,
        messages: list[ProviderMessage],
        tools: list[dict],
        model: str,
        max_tokens: int,
    ) -> AsyncIterator[ProviderEvent]:
        import httpx

        wire_messages = _to_openai_messages(system, messages)
        token_param = "max_completion_tokens" if _uses_completion_tokens(model) else "max_tokens"
        payload: dict[str, Any] = {
            "model": model,
            "messages": wire_messages,
            token_param: max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if tools:
            payload["tools"] = [_sanitize_tool_schema(t) for t in tools]
            payload["parallel_tool_calls"] = False

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        pending: dict[int, dict[str, Any]] = {}
        stop_reason = "stop"

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", self._endpoint, headers=headers, json=payload) as response:
                if response.status_code >= 400:
                    error_text = await response.aread()
                    raise LLMError(f"HTTP {response.status_code}: {error_text.decode('utf-8')}")

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    usage = chunk.get("usage")
                    if usage:
                        yield Usage(
                            input_tokens=usage.get("prompt_tokens", 0),
                            output_tokens=usage.get("completion_tokens", 0),
                        )

                    choices = chunk.get("choices")
                    if not choices:
                        continue

                    choice = choices[0]
                    delta = choice.get("delta") or {}

                    content = delta.get("content")
                    if content:
                        yield TextDelta(text=content)

                    tool_calls = delta.get("tool_calls")
                    if tool_calls:
                        for tc in tool_calls:
                            idx = tc.get("index", 0)
                            slot = pending.setdefault(
                                idx, {"id": "", "name": "", "args": "", "extra": None}
                            )
                            if tc.get("id"):
                                slot["id"] = tc["id"]
                            extra = tc.get("extra_content") or delta.get("extra_content")
                            if extra:
                                slot["extra"] = extra
                            fn = tc.get("function")
                            if fn:
                                if fn.get("name"):
                                    slot["name"] = fn["name"]
                                if fn.get("arguments"):
                                    slot["args"] += fn["arguments"]

                    finish_reason = choice.get("finish_reason")
                    if finish_reason:
                        stop_reason = finish_reason

        for slot in pending.values():
            yield ToolUse(
                id=slot["id"],
                name=_from_openai_name(slot["name"]),
                input=_parse_args(slot["args"]),
                extra=slot.get("extra"),
            )

        yield Done(stop_reason=stop_reason)


# OpenAI restricts function names to ``^[a-zA-Z0-9_-]+$``, but our tool
# registry namespaces with a dot (``patients.search_patients``). Tool /
# module names are snake_case with no hyphens, so ``.`` <-> ``-`` is a
# lossless bijection confined to this provider.
def _uses_completion_tokens(model: str) -> bool:
    """GPT-5 and the o-series require `max_completion_tokens`, not `max_tokens`."""
    m = model.lower()
    return m.startswith(("gpt-5", "o1", "o3", "o4"))


def _to_openai_name(qualified: str) -> str:
    return qualified.replace(".", "-")


def _from_openai_name(safe: str) -> str:
    return safe.replace("-", ".")


def _sanitize_tool_schema(tool: dict[str, Any]) -> dict[str, Any]:
    fn = tool.get("function", {})
    return {**tool, "function": {**fn, "name": _to_openai_name(fn["name"])}}


def _parse_args(raw: str) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _to_openai_messages(system: str, messages: list[ProviderMessage]) -> list[dict[str, Any]]:
    """Flatten neutral messages into OpenAI's wire shape.

    One neutral ``tool`` message with N result blocks expands into N
    OpenAI ``role:"tool"`` messages (one per ``tool_call_id``).
    """
    out: list[dict[str, Any]] = []
    if system:
        out.append({"role": "system", "content": system})

    for msg in messages:
        if msg.role is Role.USER:
            out.append({"role": "user", "content": _join_text(msg)})

        elif msg.role is Role.ASSISTANT:
            text = _join_text(msg)
            tool_calls = []
            for block in msg.content:
                if isinstance(block, ToolUseBlock):
                    tc_dict: dict[str, Any] = {
                        "id": block.id,
                        "type": "function",
                        "function": {
                            "name": _to_openai_name(block.name),
                            "arguments": json.dumps(block.input),
                        },
                    }
                    if block.extra:
                        tc_dict["extra_content"] = block.extra
                    tool_calls.append(tc_dict)
            wire: dict[str, Any] = {"role": "assistant", "content": text or None}
            if tool_calls:
                wire["tool_calls"] = tool_calls
            out.append(wire)

        elif msg.role is Role.TOOL:
            for block in msg.content:
                if isinstance(block, ToolResultBlock):
                    out.append(
                        {
                            "role": "tool",
                            "tool_call_id": block.tool_call_id,
                            "content": _stringify(block.content),
                        }
                    )

    return out


def _join_text(msg: ProviderMessage) -> str:
    return "".join(b.text for b in msg.content if isinstance(b, TextBlock))


def _stringify(content: Any) -> str:
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False, default=str)
