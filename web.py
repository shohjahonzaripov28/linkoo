"""Linko veb-serveri: brauzer va telefon uchun.

Ishga tushirish:
    python -m linko.web          # faqat shu kompyuterda ochiladi
    python -m linko.web --lan    # bir Wi-Fi'dagi telefon ham kira oladi
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import socket
from contextlib import suppress
from dataclasses import asdict
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from .protocol import ENCODING, MAX_LINE_BYTES, MAX_TEXT_LENGTH, Message
from .server import LOGIN_TIMEOUT, NICK_PATTERN

log = logging.getLogger("linko.web")

INDEX_FILE = Path(__file__).parent / "index.html"


def encode(msg: Message) -> str:
    return json.dumps(asdict(msg), ensure_ascii=False)


def decode(raw: str) -> Message:
    return Message.from_line(raw.encode(ENCODING))


class Room:
    """Onlayn foydalanuvchilar va xabarlarni tarqatish."""

    def __init__(self) -> None:
        self.clients: dict[str, WebSocket] = {}   # nik -> ulanish

    @staticmethod
    async def send(ws: WebSocket, msg: Message) -> None:
        await ws.send_text(encode(msg))

    async def broadcast(self, msg: Message) -> None:
        results = await asyncio.gather(
            *(self.send(ws, msg) for ws in list(self.clients.values())),
            return_exceptions=True,
        )
        for result in results:
            if isinstance(result, Exception):
                log.debug("Yuborishda xato: %r", result)


room = Room()
app = FastAPI(title="Linko")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(INDEX_FILE)


async def login(ws: WebSocket) -> str | None:
    """Birinchi xabar - kirish so'rovi. Muvaffaqiyatli bo'lsa nikni qaytaradi."""
    raw = await asyncio.wait_for(ws.receive_text(), timeout=LOGIN_TIMEOUT)
    try:
        msg = decode(raw)
    except ValueError:
        return None

    nick = msg.text.strip()
    if msg.type != "login" or not NICK_PATTERN.match(nick):
        await room.send(ws, Message.error("Nik 2-20 ta harf yoki raqamdan iborat bo'lsin."))
        return None
    if nick in room.clients:
        await room.send(ws, Message.error(f"'{nick}' nomi band. Boshqasini tanlang."))
        return None

    room.clients[nick] = ws   # tekshiruv va qo'shish orasida await yo'q -> xavfsiz
    try:
        await room.send(ws, Message.system(f"Linko'ga xush kelibsiz, {nick}! /kim - onlayn ro'yxat, /chiq - chiqish"))
    except Exception:
        room.clients.pop(nick, None)
        raise
    return nick


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    nick: str | None = None
    try:
        nick = await login(ws)
        if nick is None:
            return
        log.info("%s ulandi", nick)
        await room.broadcast(Message.system(f"{nick} chatga qo'shildi"))

        while True:
            try:
                msg = decode(await ws.receive_text())
            except ValueError:
                continue   # buzuq xabarni e'tiborsiz qoldiramiz

            text = msg.text.strip()[:MAX_TEXT_LENGTH]
            if not text:
                continue
            if text == "/kim":
                online = ", ".join(sorted(room.clients))
                await room.send(ws, Message.system(f"Onlayn ({len(room.clients)}): {online}"))
                continue

            log.info("%s: %s", nick, text)
            await room.broadcast(Message.chat(nick, text))
    except (WebSocketDisconnect, asyncio.TimeoutError, RuntimeError, KeyError):
        pass   # ulanish uzildi yoki noto'g'ri turdagi xabar keldi
    finally:
        if nick is not None:
            room.clients.pop(nick, None)
            await room.broadcast(Message.system(f"{nick} chatdan chiqdi"))
            log.info("%s chiqdi", nick)
        with suppress(Exception):
            await ws.close()


def lan_address() -> str | None:
    """Kompyuterning Wi-Fi (mahalliy tarmoq) manzilini topadi."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))   # haqiqiy paket yuborilmaydi
            return s.getsockname()[0]
    except OSError:
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Linko veb-serveri")
    parser.add_argument("--lan", action="store_true", help="bir Wi-Fi'dagi telefonlar ham kira olsin")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

    print(f"\n  Kompyuterda ochish:  http://localhost:{args.port}")
    if args.lan:
        ip = lan_address()
        if ip:
            print(f"  Telefonda ochish:    http://{ip}:{args.port}   (telefon shu Wi-Fi'da bo'lsin)")
    print()

    host = "0.0.0.0" if args.lan else "127.0.0.1"
    uvicorn.run(app, host=host, port=args.port, ws_max_size=MAX_LINE_BYTES, log_level="warning")


if __name__ == "__main__":
    main()
