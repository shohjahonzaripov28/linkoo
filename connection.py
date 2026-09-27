"""Linko klientining tarmoq qismi (oynadan mustaqil).

Tarmoq alohida oqimda (asyncio) ishlaydi. Serverdan kelgan xabarlar
`incoming` navbatiga tushadi. Oyna shu navbatni o'qib turadi.
  - Message  -> yangi xabar
  - None     -> aloqa tugadi
"""
from __future__ import annotations

import asyncio
import queue
import threading

from .protocol import MAX_LINE_BYTES, PORT, Message


class Connection:
    def __init__(self) -> None:
        self.incoming: queue.Queue[Message | None] = queue.Queue()
        self._writer: asyncio.StreamWriter | None = None
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._loop.run_forever, daemon=True).start()

    # ---------- oyna chaqiradigan metodlar ----------
    def connect(self, nick: str, host: str, port: int = PORT) -> None:
        asyncio.run_coroutine_threadsafe(self._run(nick, host, port), self._loop)

    def send(self, text: str) -> None:
        asyncio.run_coroutine_threadsafe(self._send(text), self._loop)

    def close(self) -> None:
        self._loop.call_soon_threadsafe(self._close_writer)

    # ---------- ichki qism ----------
    async def _run(self, nick: str, host: str, port: int) -> None:
        try:
            reader, writer = await asyncio.open_connection(host, port, limit=MAX_LINE_BYTES)
        except OSError as exc:
            self.incoming.put(Message.error(f"Serverga ulanib bo'lmadi ({host}:{port}): {exc}"))
            self.incoming.put(None)
            return

        self._writer = writer
        try:
            writer.write(Message("login", nick).to_bytes())
            await writer.drain()
            while line := await reader.readline():
                try:
                    self.incoming.put(Message.from_line(line))
                except ValueError:
                    continue
        except (ConnectionError, ValueError):
            pass
        finally:
            self._writer = None
            writer.close()
            self.incoming.put(None)

    async def _send(self, text: str) -> None:
        if self._writer is None:
            return
        try:
            self._writer.write(Message("chat", text).to_bytes())
            await self._writer.drain()
        except ConnectionError:
            pass

    def _close_writer(self) -> None:
        if self._writer is not None:
            self._writer.close()
