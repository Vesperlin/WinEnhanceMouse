"""Settings UI for WinEnhanceMouse."""
from __future__ import annotations

import json
import logging
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog
from typing import Dict, List

from ..actions import registry
from ..config import ActionBinding, AppConfig, ModeConfig, config_manager

logger = logging.getLogger(__name__)


class SettingsWindow:
    """Tkinter window for managing modes, bindings, and AI configuration."""

    def __init__(self, config: AppConfig) -> None:
        self._root = tk.Toplevel()
        self._root.title("WinEnhanceMouse 设置")
        self._root.geometry("720x520")
        self._config = config
        self._active_mode_index = 0

        self._build_nav()
        self._build_mode_editor()
        self._build_ai_editor()
        self._refresh_modes()

    def show(self) -> None:
        self._root.transient()
        self._root.grab_set()
        self._root.wait_window()

    # UI construction -----------------------------------------------------
    def _build_nav(self) -> None:
        nav = tk.Frame(self._root)
        nav.pack(side=tk.LEFT, fill=tk.Y)

        tk.Button(nav, text="新增模式", command=self._add_mode).pack(fill=tk.X)
        tk.Button(nav, text="删除模式", command=self._delete_mode).pack(fill=tk.X)
        tk.Button(nav, text="导入配置", command=self._import_config).pack(fill=tk.X)
        tk.Button(nav, text="导出配置", command=self._export_config).pack(fill=tk.X)

        self._mode_list = tk.Listbox(nav)
        self._mode_list.pack(fill=tk.BOTH, expand=True)
        self._mode_list.bind("<<ListboxSelect>>", lambda _: self._on_mode_select())

    def _build_mode_editor(self) -> None:
        container = tk.Frame(self._root)
        container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._primary_list = tk.Listbox(container)
        self._primary_list.pack(fill=tk.BOTH, expand=True)
        primary_buttons = tk.Frame(container)
        primary_buttons.pack(fill=tk.X)
        tk.Button(primary_buttons, text="添加一层操作", command=lambda: self._add_action(self._primary_list, 1)).pack(side=tk.LEFT)
        tk.Button(primary_buttons, text="移除", command=lambda: self._remove_action(self._primary_list, 1)).pack(side=tk.LEFT)

        self._secondary_list = tk.Listbox(container)
        self._secondary_list.pack(fill=tk.BOTH, expand=True)
        secondary_buttons = tk.Frame(container)
        secondary_buttons.pack(fill=tk.X)
        tk.Button(secondary_buttons, text="添加二层操作", command=lambda: self._add_action(self._secondary_list, 2)).pack(side=tk.LEFT)
        tk.Button(secondary_buttons, text="移除", command=lambda: self._remove_action(self._secondary_list, 2)).pack(side=tk.LEFT)

        tk.Button(container, text="应用修改", command=self._apply_changes).pack(fill=tk.X, pady=8)

    def _build_ai_editor(self) -> None:
        ai_frame = tk.LabelFrame(self._root, text="AI 设置", padx=8, pady=8)
        ai_frame.pack(side=tk.RIGHT, fill=tk.Y)

        config = self._config.ai
        self._ai_enabled = tk.BooleanVar(value=config.enabled)
        self._ai_model = tk.StringVar(value=config.model)
        self._ai_key = tk.StringVar(value=config.api_key)
        self._ai_prompt = tk.StringVar(value=config.system_prompt)

        tk.Checkbutton(ai_frame, text="启用 AI", variable=self._ai_enabled).pack(anchor="w")
        tk.Label(ai_frame, text="模型").pack(anchor="w")
        tk.Entry(ai_frame, textvariable=self._ai_model).pack(fill=tk.X)
        tk.Label(ai_frame, text="API Key").pack(anchor="w")
        tk.Entry(ai_frame, textvariable=self._ai_key, show="*").pack(fill=tk.X)
        tk.Label(ai_frame, text="系统提示词").pack(anchor="w")
        tk.Entry(ai_frame, textvariable=self._ai_prompt).pack(fill=tk.X)

    # Mode management -----------------------------------------------------
    def _refresh_modes(self) -> None:
        self._mode_list.delete(0, tk.END)
        for mode in self._config.modes:
            self._mode_list.insert(tk.END, mode.name)
        if self._config.modes:
            self._mode_list.select_set(self._active_mode_index)
            self._populate_bindings(self._config.modes[self._active_mode_index])

    def _populate_bindings(self, mode: ModeConfig) -> None:
        self._primary_list.delete(0, tk.END)
        self._secondary_list.delete(0, tk.END)
        for binding in mode.primary_queue:
            self._primary_list.insert(tk.END, f"{binding.label} ({binding.id})")
        for binding in mode.secondary_queue:
            self._secondary_list.insert(tk.END, f"{binding.label} ({binding.id})")

    def _add_mode(self) -> None:
        name = simpledialog.askstring("新增模式", "请输入模式名称：", parent=self._root)
        if not name:
            return
        self._config.modes.append(ModeConfig(name=name))
        self._active_mode_index = len(self._config.modes) - 1
        self._refresh_modes()

    def _delete_mode(self) -> None:
        if not self._config.modes:
            return
        index = self._mode_list.curselection()
        if not index:
            return
        idx = index[0]
        if messagebox.askyesno("确认删除", f"确定删除模式 {self._config.modes[idx].name} 吗？"):
            del self._config.modes[idx]
            self._active_mode_index = max(0, idx - 1)
            self._refresh_modes()

    def _on_mode_select(self) -> None:
        selection = self._mode_list.curselection()
        if not selection:
            return
        self._active_mode_index = selection[0]
        self._populate_bindings(self._config.modes[self._active_mode_index])

    def _add_action(self, listbox: tk.Listbox, level: int) -> None:
        available = sorted(registry.ids())
        action = simpledialog.askstring("添加操作", f"请输入操作 ID：\n可选：{', '.join(available)}", parent=self._root)
        if not action:
            return
        label = simpledialog.askstring("显示名称", "请输入显示名称：", parent=self._root) or action
        params_input = simpledialog.askstring("参数", "请输入 JSON 参数（可选）：", parent=self._root)
        params: Dict[str, object] = {}
        if params_input:
            try:
                params = json.loads(params_input)
            except json.JSONDecodeError as exc:
                messagebox.showerror("格式错误", f"JSON 解析失败：{exc}")
                return
        binding = ActionBinding(id=action, label=label, params=params)
        mode = self._config.modes[self._active_mode_index]
        if level == 1:
            mode.primary_queue.append(binding)
        else:
            mode.secondary_queue.append(binding)
        listbox.insert(tk.END, f"{binding.label} ({binding.id})")

    def _remove_action(self, listbox: tk.Listbox, level: int) -> None:
        selection = listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        mode = self._config.modes[self._active_mode_index]
        if level == 1:
            del mode.primary_queue[idx]
        else:
            del mode.secondary_queue[idx]
        listbox.delete(idx)

    # Persistence ---------------------------------------------------------
    def _apply_changes(self) -> None:
        mode = self._config.modes[self._active_mode_index]
        new_primary: List[ActionBinding] = []
        for entry in self._primary_list.get(0, tk.END):
            new_primary.append(self._resolve_binding(entry, mode.primary_queue))
        new_secondary: List[ActionBinding] = []
        for entry in self._secondary_list.get(0, tk.END):
            new_secondary.append(self._resolve_binding(entry, mode.secondary_queue))
        mode.primary_queue = new_primary
        mode.secondary_queue = new_secondary
        ai = self._config.ai
        ai.enabled = self._ai_enabled.get()
        ai.model = self._ai_model.get()
        ai.api_key = self._ai_key.get()
        ai.system_prompt = self._ai_prompt.get()
        config_manager.save(self._config)
        messagebox.showinfo("保存成功", "配置已保存并立即生效。")

    def _resolve_binding(self, label: str, source: List[ActionBinding]) -> ActionBinding:
        for binding in source:
            if binding.label in label:
                return binding
        raise ValueError(f"无法解析绑定：{label}")

    def _import_config(self) -> None:
        path = simpledialog.askstring("导入配置", "请输入配置文件路径：", parent=self._root)
        if not path:
            return
        try:
            loaded = config_manager.load(Path(path))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("导入失败", str(exc))
            return
        self._config.modes = loaded.modes
        self._config.menu = loaded.menu
        self._config.ai = loaded.ai
        self._active_mode_index = 0
        self._refresh_modes()
        messagebox.showinfo("导入成功", "配置已导入。")

    def _export_config(self) -> None:
        path = simpledialog.askstring("导出配置", "请输入导出路径：", parent=self._root)
        if not path:
            return
        target = Path(path)
        try:
            config_manager.save(self._config, target)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("导出失败", str(exc))
            return
        messagebox.showinfo("导出成功", f"配置已导出到 {target}")


__all__ = ["SettingsWindow"]
