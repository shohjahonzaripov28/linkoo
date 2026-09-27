"""Linko chat serveri.

Ishga tushirish:  python -m linko.server
"""
from __future__ import annotations

import asyncio
import logging
import re
from contextlib import suppress

from .protocol import HOST, MAX_LINE_BYTES, MAX_TEXT_LENGTH, PORT, Message

log = logging.getLogger("linko.server")

NICK_PATTERN = re.compile(r"^\w{2,20}$")   # 2-20 ta harf/raqam/_ (kirill va xitoycha ham mumkin)
LOGIN_TIMEOUT = 30                          # soniya


class ChatServer:
    def __init__(self, host: str = HOST, port: int = PORT) -> None:
        self.host = host
        self.port = port
        self.clients: dict[str, asyncio.StreamWriter] = {}   # nik -> ulanish

    async def start(self) -> None:
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port, limit=MAX_LINE_BYTES
        )
        addresses = ", ".join(str(s.getsockname()) for s in server.sockets)
        log.info("Server ishga tushdi: %s", addresses)
        async with server:
            await server.serve_forever()

    # ---------- yuborish ----------
    @staticmethod
    async def _send(writer: asyncio.StreamWriter, msg: Message) -> None:
        writer.write(msg.to_bytes())
        await writer.drain()

    async def broadcast(self, msg: Message) -> None:
        """Xabarni hamma onlayn foydalanuvchiga yuboradi."""
        writers = list(self.clients.values())
        results = await asyncio.gather(
            *(self._send(w, msg) for w in writers), return_exceptions=True
        )
        for result in results:
            if isinstance(result, Exception):
                # uzilgan ulanishni o'sha klientning o'z handler'i tozalaydi
                log.debug("Yuborishda xato: %r", result)

    # ---------- bitta klient bilan ishlash ----------
    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        peer = writer.get_extra_info("peername")
        nick: str | None = None
        try:
            nick = await self._login(reader, writer)
            if nick is None:
                return
            log.info("%s ulandi (%s)", nick, peer)
            await self.broadcast(Message.system(f"{nick} chatga qo'shildi"))
            await self._chat_loop(nick, reader, writer)
        except (ConnectionError, asyncio.TimeoutError, ValueError):
            log.info("Ulanish uzildi: %s", peer)
        finally:
            if nick is not None:
                self.clients.pop(nick, None)
                await self.broadcast(Message.system(f"{nick} chatdan chiqdi"))
                log.info("%s chiqdi", nick)
            writer.close()
            with suppress(ConnectionError):
                await writer.wait_closed()

    async def _login(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> str | None:
        line = await asyncio.wait_for(reader.readline(), timeout=LOGIN_TIMEOUT)
        if not line:
            return None
        try:
            msg = Message.from_line(line)
        except ValueError:
            return None

        nick = msg.text.strip()
        if msg.type != "login" or not NICK_PATTERN.match(nick):
            await self._send(writer, Message.error("Nik 2-20 ta harf yoki raqamdan iborat bo'lsin."))
            return None
        if nick in self.clients:
            await self._send(writer, Message.error(f"'{nick}' nomi band. Boshqasini tanlang."))
            return None

        self.clients[nick] = writer   # tekshiruv va qo'shish orasida await yo'q -> xavfsiz
        await self._send(writer, Message.system(f"Linko'ga xush kelibsiz, {nick}! /kim - onlayn ro'yxat, /chiq - chiqish"))
        return nick

    async def _chat_loop(
        self, nick: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        while line := await reader.readline():
            try:
                msg = Message.from_line(line)
            except ValueError:
                continue   # buzuq xabarni e'tiborsiz qoldiramiz

            text = msg.text.strip()[:MAX_TEXT_LENGTH]
            if not text:
                continue
            if text == "/kim":
                online = ", ".join(sorted(self.clients))
                await self._send(writer, Message.system(f"Onlayn ({len(self.clients)}): {online}"))
                continue

            log.info("%s: %s", nick, text)
            await self.broadcast(Message.chat(nick, text))


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    try:
        asyncio.run(ChatServer().start())
    except KeyboardInterrupt:
        log.info("Server to'xtatildi")


if __name__ == "__main__":
    main()
