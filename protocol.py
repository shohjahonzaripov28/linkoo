"""Linko protokoli: server va klient o'rtasidagi xabar formati.

Har bir xabar - bitta JSON qator (oxirida '\\n'). Bu usul oddiy va
xatolarni topish oson: qatorni o'qiysiz -> JSON'ni ochasiz -> tayyor.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime

HOST = "127.0.0.1"
PORT = 8888
ENCODING = "utf-8"
MAX_LINE_BYTES = 4096      # bitta xabar qatorining eng katta hajmi
MAX_TEXT_LENGTH = 1000     # xabar matnining eng katta uzunligi


def timestamp() -> str:
    return datetime.now().strftime("%H:%M")


@dataclass(frozen=True)
class Message:
    type: str              # "login" | "chat" | "system" | "error"
    text: str
    sender: str = ""
    time: str = field(default_factory=timestamp)

    # --- qulay "fabrika" metodlari ---
    @classmethod
    def chat(cls, sender: str, text: str) -> "Message":
        return cls("chat", text, sender)

    @classmethod
    def system(cls, text: str) -> "Message":
        return cls("system", text)

    @classmethod
    def error(cls, text: str) -> "Message":
        return cls("error", text)

    # --- tarmoq uchun aylantirish ---
    def to_bytes(self) -> bytes:
        payload = json.dumps(asdict(self), ensure_ascii=False)
        return (payload + "\n").encode(ENCODING)

    @classmethod
    def from_line(cls, line: bytes) -> "Message":
        """Qatorni Message'ga aylantiradi. Xato bo'lsa ValueError ko'taradi."""
        try:
            data = json.loads(line.decode(ENCODING))
            return cls(
                type=str(data["type"]),
                text=str(data["text"]),
                sender=str(data.get("sender", "")),
                time=str(data.get("time") or timestamp()),
            )
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise ValueError(f"Noto'g'ri xabar: {exc}") from exc
