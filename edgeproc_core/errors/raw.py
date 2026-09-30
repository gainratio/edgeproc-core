"""Duck-typing helpers for reading a raw failure of unknown shape.

A raw failure might be a thrown ``Exception``, an httpx/requests response-like
object with ``.status_code``, a fetch-style object with ``.status``, a plain
``Mapping``, or a bare string — so we probe defensively and never assume a class.
These are exported so authors can reuse them inside their own ``match`` rules.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeGuard

_STATUS_KEYS = ("status_code", "status")
_TEXT_KEYS = ("message", "body")
_MAX_RESPONSE_HOPS = 3  # bounds the walk, so a cyclic ``.response`` cannot loop forever


def _read(raw: object, key: str) -> object:
    """Read ``key`` from a mapping item or an object attribute, or ``None``."""
    if isinstance(raw, Mapping):
        item: object = raw.get(key)
        return item
    attr: object = getattr(raw, key, None)
    return attr


def _is_status(value: object) -> TypeGuard[int]:
    """A real HTTP status: an ``int`` that is not a ``bool``."""
    return isinstance(value, int) and not isinstance(value, bool)


def _direct_status(raw: object) -> int | None:
    """The status on ``raw`` itself (``status_code`` first, then ``status``), or ``None``."""
    for key in _STATUS_KEYS:
        value = _read(raw, key)
        if _is_status(value):
            return value
    return None


def http_status_of(raw: object) -> int | None:
    """The numeric HTTP status on a raw failure (httpx/requests/fetch), or ``None``.

    A status on ``raw`` itself wins. Otherwise follow a nested ``response`` (the shape of
    ``requests.HTTPError`` and ``httpx.HTTPStatusError``), at most ``_MAX_RESPONSE_HOPS`` deep.
    """
    current = raw
    for _ in range(_MAX_RESPONSE_HOPS + 1):
        status = _direct_status(current)
        if status is not None:
            return status
        current = _read(current, "response")
    return None


def error_name_of(raw: object) -> str:
    """The failure's name — a ``.name`` attr, else the exception class name, else ``""``."""
    name = _read(raw, "name")
    if isinstance(name, str):
        return name
    if isinstance(raw, BaseException):
        return type(raw).__name__
    return ""


def _text_parts(raw: object) -> list[str]:
    """The string ``message`` / ``body`` fragments carried on a raw failure."""
    parts: list[str] = []
    for key in _TEXT_KEYS:
        value = _read(raw, key)
        if isinstance(value, str):
            parts.append(value)
    return parts


def error_text_of(raw: object) -> str:
    """Searchable text — a string raw, its message/body, or the exception ``str``."""
    if isinstance(raw, str):
        return raw
    parts = _text_parts(raw)
    if not parts and isinstance(raw, BaseException):
        return str(raw)
    return " ".join(parts)
