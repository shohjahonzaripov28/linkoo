"""Linko chat klienti.

Ishga tushirish:  python -m linko.client
"""
from __future__ import annotations

import asyncio
import sys
import threading

from .protocol import HOST, MAX_LINE_BYTES, PORT, Message


def format_message(msg: Message) -> str:
    if msg.type == "chat":
        return f"[{msg.time}] {msg.sender}: {msg.text}"
    if msg.type == "error":
        return f"! {msg.text}"
    return f"* {msg.text}"


async def receive(reader: asyncio.StreamReader) -> None:
    """Serverdan kelgan xabarlarni ekranga chiqaradi."""
    while line := await reader.readline():
        try:
            print(format_message(Message.from_line(line)))
        except ValueError:
            continue
    print("* Server bilan aloqa uzildi.")


def start_stdin_thread(loop: asyncio.AbstractEventLoop, queue: asyncio.Queue) -> None:
    """input() to'xtatib turadi, shuning uchun uni alohida oqimda o'qiymiz."""
    def worker() -> None:
        for line in sys.stdin:
            loop.call_soon_threadsafe(queue.put_nowait, line.rstrip("\n"))
        loop.call_soon_threadsafe(queue.put_nowait, None)   # stdin yopildi

    threading.Thread(target=worker, daemon=True).start()


async def send(writer: asyncio.StreamWriter, queue: asyncio.Queue) -> None:
    """Klaviaturadan yozilganini serverga yuboradi."""
    while (text := await queue.get()) is not None:
        if text.strip() == "/chiq":
            return
        if text.strip():
            writer.write(Message("chat", text).to_bytes())
            await writer.drain()


async def run(nick: str, host: str = HOST, port: int = PORT) -> None:
    try:
        reader, writer = await asyncio.open_connection(host, port, limit=MAX_LINE_BYTES)
    except OSError as exc:
        print(f"Serverga ulanib bo'lmadi ({host}:{port}): {exc}")
        return

    writer.write(Message("login", nick).to_bytes())
    await writer.drain()

    queue: asyncio.Queue = asyncio.Queue()
    start_stdin_thread(asyncio.get_running_loop(), queue)

    tasks = [asyncio.create_task(receive(reader)), asyncio.create_task(send(writer, queue))]
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for task in tasks:
            task.cancel()
        writer.close()


def main() -> None:
    nick = input("Nikingiz: ").strip()
    try:
        asyncio.run(run(nick))
    except KeyboardInterrupt:
        pass
    print("Xayr!")


if __name__ == "__main__":
    main()
