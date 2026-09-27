"""Linko - oynali (Tkinter) klient.

Ishga tushirish:  python -m linko.gui
(Avval boshqa oynada server ishlab turishi kerak: python -m linko.server)
"""
from __future__ import annotations

import queue
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from .connection import Connection
from .protocol import HOST, Message

FONT = ("Segoe UI", 11)
FONT_BOLD = ("Segoe UI", 11, "bold")
FONT_SMALL = ("Segoe UI", 9)
POLL_MS = 100   # navbatni qanchalik tez-tez tekshirish (millisoniya)


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Linko")
        self.geometry("480x620")
        self.minsize(360, 420)

        self.conn: Connection | None = None
        self.nick = ""
        self.in_chat = False

        self._build_login()
        self._build_chat()
        self.login_frame.pack(fill="both", expand=True)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(POLL_MS, self._poll)

    # ---------- oynalarni qurish ----------
    def _build_login(self) -> None:
        f = self.login_frame = ttk.Frame(self, padding=30)

        ttk.Label(f, text="Linko", font=("Segoe UI", 32, "bold")).pack(pady=(60, 4))
        ttk.Label(f, text="Chatga kirish", font=FONT).pack(pady=(0, 30))

        ttk.Label(f, text="Nikingiz", font=FONT).pack(anchor="w")
        self.nick_var = tk.StringVar()
        nick_entry = ttk.Entry(f, textvariable=self.nick_var, font=FONT)
        nick_entry.pack(fill="x", pady=(2, 14))

        ttk.Label(f, text="Server manzili", font=FONT).pack(anchor="w")
        self.host_var = tk.StringVar(value=HOST)
        host_entry = ttk.Entry(f, textvariable=self.host_var, font=FONT)
        host_entry.pack(fill="x", pady=(2, 20))

        self.login_btn = ttk.Button(f, text="Kirish", command=self._login)
        self.login_btn.pack(fill="x", ipady=6)

        self.status_var = tk.StringVar()
        ttk.Label(f, textvariable=self.status_var, font=FONT_SMALL,
                  foreground="#c0392b", wraplength=380).pack(pady=14)

        for entry in (nick_entry, host_entry):
            entry.bind("<Return>", self._login)
        nick_entry.focus_set()

    def _build_chat(self) -> None:
        f = self.chat_frame = ttk.Frame(self, padding=8)

        top = ttk.Frame(f)
        top.pack(fill="x", pady=(0, 6))
        ttk.Label(top, text="Linko", font=("Segoe UI", 14, "bold")).pack(side="left")
        ttk.Button(top, text="Chiqish", command=self._leave).pack(side="right")
        ttk.Button(top, text="Onlayn", command=lambda: self._send_command("/kim")).pack(side="right", padx=6)

        self.text = ScrolledText(f, state="disabled", wrap="word", font=FONT,
                                 relief="flat", borderwidth=1, padx=8, pady=8)
        self.text.pack(fill="both", expand=True)
        self.text.tag_configure("time", foreground="#95a5a6", font=FONT_SMALL)
        self.text.tag_configure("me", foreground="#2980b9", font=FONT_BOLD)
        self.text.tag_configure("other", foreground="#27ae60", font=FONT_BOLD)
        self.text.tag_configure("system", foreground="#7f8c8d", font=(FONT[0], FONT[1], "italic"))
        self.text.tag_configure("error", foreground="#c0392b")

        bottom = ttk.Frame(f)
        bottom.pack(fill="x", pady=(8, 0))
        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(bottom, textvariable=self.entry_var, font=FONT)
        self.entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.entry.bind("<Return>", self._send)
        ttk.Button(bottom, text="Yuborish", command=self._send).pack(side="right", padx=(6, 0))

    # ---------- ekranlar almashishi ----------
    def _show_chat(self) -> None:
        self.login_frame.pack_forget()
        self.chat_frame.pack(fill="both", expand=True)
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")
        self.in_chat = True
        self.status_var.set("")
        self.entry.focus_set()

    def _back_to_login(self, status: str = "") -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None      # eski ulanishdan kelgan xabarlar endi o'qilmaydi
        self.in_chat = False
        self.chat_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)
        self.login_btn.configure(state="normal")
        self.status_var.set(status)

    # ---------- tugmalar ----------
    def _login(self, event=None) -> None:
        nick = self.nick_var.get().strip()
        host = self.host_var.get().strip() or HOST
        if not nick:
            self.status_var.set("Avval nik yozing.")
            return
        self.nick = nick
        self.status_var.set("Ulanmoqda...")
        self.login_btn.configure(state="disabled")
        self.conn = Connection()
        self.conn.connect(nick, host)

    def _send(self, event=None) -> None:
        text = self.entry_var.get().strip()
        if not text or self.conn is None:
            return
        self.entry_var.set("")
        if text == "/chiq":
            self._leave()
        else:
            self.conn.send(text)

    def _send_command(self, command: str) -> None:
        if self.conn is not None:
            self.conn.send(command)

    def _leave(self) -> None:
        self._back_to_login("Chatdan chiqdingiz.")

    def _on_close(self) -> None:
        if self.conn is not None:
            self.conn.close()
        self.destroy()

    # ---------- serverdan kelgan xabarlarni qabul qilish ----------
    def _poll(self) -> None:
        conn = self.conn
        if conn is not None:
            while conn is self.conn:          # _back_to_login ulanishni almashtirsa, to'xtaymiz
                try:
                    msg = conn.incoming.get_nowait()
                except queue.Empty:
                    break
                self._handle(msg)
        self.after(POLL_MS, self._poll)

    def _handle(self, msg: Message | None) -> None:
        if msg is None:                        # aloqa tugadi
            self._back_to_login("Server bilan aloqa uzildi.")
            return
        if not self.in_chat:
            if msg.type == "system":           # server kirishni qabul qildi
                self._show_chat()
            else:                              # nik band, noto'g'ri nik va h.k.
                self._back_to_login(msg.text)
                return
        self._append(msg)

    def _append(self, msg: Message) -> None:
        self.text.configure(state="normal")
        if msg.type == "chat":
            tag = "me" if msg.sender == self.nick else "other"
            self.text.insert("end", f"[{msg.time}] ", "time")
            self.text.insert("end", f"{msg.sender}: ", tag)
            self.text.insert("end", msg.text + "\n")
        else:
            prefix = "! " if msg.type == "error" else "* "
            self.text.insert("end", prefix + msg.text + "\n", msg.type)
        self.text.configure(state="disabled")
        self.text.see("end")


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
