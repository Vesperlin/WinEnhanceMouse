"""Simple AI assistant chat window."""
from __future__ import annotations

import logging
import tkinter as tk
from tkinter import scrolledtext

from ..ai import AIAssistant

logger = logging.getLogger(__name__)


class AIWindow:
    def __init__(self, assistant: AIAssistant) -> None:
        self._assistant = assistant
        self._root = tk.Toplevel()
        self._root.title("WinEnhanceMouse AI 助手")
        self._root.geometry("520x420")
        self._conversation = scrolledtext.ScrolledText(self._root, state=tk.DISABLED)
        self._conversation.pack(fill=tk.BOTH, expand=True)
        self._input = tk.Text(self._root, height=4)
        self._input.pack(fill=tk.X)
        tk.Button(self._root, text="发送", command=self._on_send).pack(anchor="e")

    def show(self) -> None:
        self._root.transient()
        self._root.grab_set()
        self._root.wait_window()

    def _append(self, speaker: str, text: str) -> None:
        self._conversation.configure(state=tk.NORMAL)
        self._conversation.insert(tk.END, f"{speaker}: {text}\n")
        self._conversation.configure(state=tk.DISABLED)
        self._conversation.see(tk.END)

    def _on_send(self) -> None:
        text = self._input.get("1.0", tk.END).strip()
        if not text:
            return
        self._append("用户", text)
        self._input.delete("1.0", tk.END)
        try:
            reply = self._assistant.chat([{ "role": "user", "content": text }])
        except Exception as exc:  # noqa: BLE001
            logger.exception("AI 调用失败")
            reply = f"调用失败: {exc}"
        self._append("AI", reply)


__all__ = ["AIWindow"]
