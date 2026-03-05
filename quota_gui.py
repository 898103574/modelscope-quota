#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ModelScope 配额查询器 - 桌面应用程序
支持添加/删除模型，刷新配额
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import json
import os
from datetime import datetime

# ==================== 配置路径 ====================
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# ==================== 默认配置 ====================
DEFAULT_CONFIG = {
    "api_key": "ms-97ecf3f3-449a-474a-a32f-d3d6fd48f613",
    "api_url": "https://api-inference.modelscope.cn/v1/chat/completions",
    "models": []  # 存储模型ID列表
}

# ==================== 配置文件操作 ====================
def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # 确保所有字段都存在
                for key in DEFAULT_CONFIG:
                    if key not in config:
                        config[key] = DEFAULT_CONFIG[key]
                return config
        except Exception as e:
            print(f"加载配置失败: {e}")
    return DEFAULT_CONFIG.copy()


def save_config(config):
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False


# ==================== 配额查询 ====================
def query_quota(api_key, api_url, model_id, max_retries=3):
    """查询单个模型的配额"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "OpenClaw/1.0",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": "quota"}],
        "max_tokens": 1
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(api_url, headers=headers, json=data, timeout=15)
            
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}: {response.text[:100]}"}
            
            model_limit = response.headers.get('Modelscope-Ratelimit-Model-Requests-Limit')
            model_remaining = response.headers.get('Modelscope-Ratelimit-Model-Requests-Remaining')
            account_limit = response.headers.get('Modelscope-Ratelimit-Requests-Limit')
            account_remaining = response.headers.get('Modelscope-Ratelimit-Requests-Remaining')
            
            return {
                "model": {
                    "name": model_id,
                    "limit": int(model_limit) if model_limit else None,
                    "remaining": int(model_remaining) if model_remaining else None,
                    "used": (int(model_limit) - int(model_remaining)) if (model_limit and model_remaining) else None
                },
                "account": {
                    "limit": int(account_limit) if account_limit else None,
                    "remaining": int(account_remaining) if account_remaining else None,
                    "used": (int(account_limit) - int(account_remaining)) if (account_limit and account_remaining) else None
                },
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            if attempt < max_retries - 1:
                continue
            return {"error": str(e)}
    
    return {"error": "请求超时"}


def query_account_quota(api_key, api_url):
    """查询账户总配额"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "OpenClaw/1.0",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "Qwen/Qwen3-8B-Chat",
        "messages": [{"role": "user", "content": "test"}],
        "max_tokens": 1
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=15)
        account_limit = response.headers.get('Modelscope-Ratelimit-Requests-Limit')
        account_remaining = response.headers.get('Modelscope-Ratelimit-Requests-Remaining')
        
        return {
            "limit": int(account_limit) if account_limit else None,
            "remaining": int(account_remaining) if account_remaining else None,
            "used": (int(account_limit) - int(account_remaining)) if (account_limit and account_remaining) else None
        }
    except Exception as e:
        return {"error": str(e)}


# ==================== 界面类 ====================
class QuotaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ModelScope 配额查询器")
        self.root.geometry("750x500")
        self.root.resizable(True, True)
        
        # 加载配置
        self.config = load_config()
        
        # 模型列表
        self.models = []  # 存储 (model_id, quota_data) 元组
        self.selected_model = None
        
        self.setup_ui()
        self.setup_context_menu()
        
        # 加载保存的模型并查询
        self.load_saved_models()
        
        # 启动时查询账户配额
        self.after_init()
    
    def load_saved_models(self):
        """加载保存的模型（不自动查询）"""
        saved_models = self.config.get("models", [])
        for model_id in saved_models:
            # 仅加载模型列表，不查询配额
            self.models.append((model_id, None))
        self.refresh_model_list()
    
    def after_init(self):
        """初始化完成后查询账户配额"""
        self.refresh_account_quota()
    
    def setup_ui(self):
        """设置界面布局"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ===== 账户总配额区域 =====
        account_frame = ttk.LabelFrame(main_frame, text="账户总配额", padding="10")
        account_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 账户配额表格（无操作列）
        account_cols = ("总额度", "已使用", "剩余", "使用率")
        self.account_tree = ttk.Treeview(account_frame, columns=account_cols, show="headings", height=1)
        for col in account_cols:
            self.account_tree.heading(col, text=col)
            self.account_tree.column(col, width=120, anchor="center")
        
        self.account_tree.pack(fill=tk.X)
        
        # 初始化账户配额行
        self.account_tree.insert("", tk.END, values=("-", "-", "-", "-"))
        
        # 刷新账户配额按钮
        btn_frame = ttk.Frame(account_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(btn_frame, text="刷新账户配额", command=self.refresh_account_quota).pack(side=tk.LEFT)
        
        # ===== 模型配额区域 =====
        model_frame = ttk.LabelFrame(main_frame, text="模型配额", padding="10")
        model_frame.pack(fill=tk.BOTH, expand=True)
        
        # 表格
        model_cols = ("模型ID", "总额度", "已使用", "剩余", "使用率")
        self.model_tree = ttk.Treeview(model_frame, columns=model_cols, show="headings", height=8)
        
        self.model_tree.heading("模型ID", text="模型ID")
        self.model_tree.heading("总额度", text="总额度")
        self.model_tree.heading("已使用", text="已使用")
        self.model_tree.heading("剩余", text="剩余")
        self.model_tree.heading("使用率", text="使用率")
        
        self.model_tree.column("模型ID", width=280, anchor="w")
        self.model_tree.column("总额度", width=100, anchor="center")
        self.model_tree.column("已使用", width=100, anchor="center")
        self.model_tree.column("剩余", width=100, anchor="center")
        self.model_tree.column("使用率", width=100, anchor="center")
        
        # 选中行事件
        self.model_tree.bind("<<TreeviewSelect>>", self.on_model_select)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(model_frame, orient=tk.VERTICAL, command=self.model_tree.yview)
        self.model_tree.configure(yscrollcommand=scrollbar.set)
        
        self.model_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ===== 底部操作区域 =====
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 添加模型输入框
        ttk.Label(bottom_frame, text="模型ID:").pack(side=tk.LEFT, padx=(0, 5))
        self.model_id_entry = ttk.Entry(bottom_frame, width=40)
        self.model_id_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.model_id_entry.bind("<Return>", lambda e: self.add_model_from_entry())
        
        # 添加按钮
        ttk.Button(bottom_frame, text="添加模型", command=self.add_model_from_entry).pack(side=tk.LEFT, padx=(0, 10))
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="gray")
        status_label.pack(fill=tk.X, pady=(5, 0))
    
    def setup_context_menu(self):
        """设置右键菜单"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="刷新", command=self.refresh_selected_model)
        self.context_menu.add_command(label="复制模型ID", command=self.copy_model_id)
        self.context_menu.add_command(label="删除", command=self.delete_selected_model)
        
        # 绑定右键事件
        self.model_tree.bind("<Button-3>", self.show_context_menu)
        self.model_tree.bind("<ButtonRelease-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        # 选中点击的行
        item = self.model_tree.identify_row(event.y)
        if item:
            self.model_tree.selection_set(item)
            self.on_model_select(None)
            self.context_menu.post(event.x_root, event.y_root)
    
    def on_model_select(self, event):
        """模型选中事件"""
        selection = self.model_tree.selection()
        if selection:
            self.selected_model = self.model_tree.item(selection[0])["values"][0]
        else:
            self.selected_model = None
    
    def add_model_from_entry(self):
        """从输入框添加模型（不自动查询）"""
        model_id = self.model_id_entry.get().strip()
        if not model_id:
            messagebox.showwarning("警告", "请输入模型ID")
            return
        
        if len(self.models) >= 10:
            messagebox.showwarning("警告", "最多只能添加 10 个模型")
            return
        
        # 检查是否已存在
        for existing_id, _ in self.models:
            if existing_id == model_id:
                messagebox.showwarning("警告", "该模型已添加")
                return
        
        # 直接添加模型，不查询配额
        self.models.append((model_id, None))
        self.refresh_model_list()
        self.save_models_to_config()
        self.model_id_entry.delete(0, tk.END)
        self.status_var.set(f"已添加 {model_id}，点击刷新获取配额")
    
    def add_model(self, model_id, save=True):
        """添加模型并查询配额"""
        if len(self.models) >= 10:
            return False
        
        self.status_var.set(f"正在查询 {model_id}...")
        self.model_id_entry.config(state=tk.DISABLED)
        
        def query():
            quota = query_quota(
                self.config["api_key"],
                self.config["api_url"],
                model_id
            )
            self.root.after(0, lambda: self.on_model_added(model_id, quota, save))
        
        thread = threading.Thread(target=query, daemon=True)
        thread.start()
        return True
    
    def on_model_added(self, model_id, quota, save):
        """模型添加完成回调"""
        self.model_id_entry.config(state=tk.NORMAL)
        
        if "error" in quota:
            # 不弹窗，只在状态栏显示错误
            self.status_var.set(f"查询失败: {quota['error']}")
            # 仍然添加到列表中
            self.models.append((model_id, quota))
            self.refresh_model_list()
            if save:
                self.save_models_to_config()
            return
        
        self.models.append((model_id, quota))
        self.refresh_model_list()
        
        # 保存到配置
        if save:
            self.save_models_to_config()
        
        # 如果是第一个模型，同时更新账户配额
        if len(self.models) == 1 and "account" in quota:
            self.update_account_display(quota["account"])
        
        self.status_var.set(f"已添加 {model_id}")
    
    def save_models_to_config(self):
        """保存模型列表到配置"""
        model_ids = [mid for mid, _ in self.models]
        self.config["models"] = model_ids
        save_config(self.config)
    
    def delete_selected_model(self):
        """删除选中的模型"""
        if not self.selected_model:
            return
        
        if messagebox.askyesno("确认", f"确定要删除模型 {self.selected_model} 吗?"):
            self.delete_model(self.selected_model)
    
    def delete_model(self, model_id):
        """删除模型"""
        self.models = [(mid, q) for mid, q in self.models if mid != model_id]
        self.refresh_model_list()
        self.selected_model = None
        
        # 更新配置
        self.save_models_to_config()
        
        self.status_var.set(f"已删除 {model_id}")
    
    def refresh_selected_model(self):
        """刷新选中的模型"""
        if self.selected_model:
            self.refresh_model(self.selected_model)
    
    def copy_model_id(self):
        """复制选中的模型ID到剪贴板"""
        if self.selected_model:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.selected_model)
            self.status_var.set(f"已复制: {self.selected_model}")
    
    def refresh_model(self, model_id):
        """刷新单个模型配额"""
        self.status_var.set(f"正在刷新 {model_id}...")
        
        def query():
            quota = query_quota(
                self.config["api_key"],
                self.config["api_url"],
                model_id
            )
            self.root.after(0, lambda: self.on_model_refreshed(model_id, quota))
        
        thread = threading.Thread(target=query, daemon=True)
        thread.start()
    
    def on_model_refreshed(self, model_id, quota):
        """模型刷新完成回调"""
        if "error" in quota:
            # 不弹窗，只在状态栏显示错误
            self.status_var.set(f"刷新失败: {quota['error']}")
            # 仍然更新列表中的数据
            for i, (mid, _) in enumerate(self.models):
                if mid == model_id:
                    self.models[i] = (model_id, quota)
                    break
            self.refresh_model_list()
            return
        
        # 更新模型数据
        for i, (mid, _) in enumerate(self.models):
            if mid == model_id:
                self.models[i] = (model_id, quota)
                break
        
        self.refresh_model_list()
        
        # 如果是选中的模型，保持选中状态
        if self.selected_model == model_id:
            for item in self.model_tree.get_children():
                if self.model_tree.item(item)["values"][0] == model_id:
                    self.model_tree.selection_set(item)
                    break
        
        # 如果是第一个模型，同时更新账户配额
        if len(self.models) > 0 and self.models[0][0] == model_id and "account" in quota:
            self.update_account_display(quota["account"])
        
        self.status_var.set(f"已刷新 {model_id}")
    
    def refresh_account_quota(self):
        """刷新账户总配额"""
        self.status_var.set("正在刷新账户配额...")
        
        def query():
            quota = query_account_quota(
                self.config["api_key"],
                self.config["api_url"]
            )
            self.root.after(0, lambda: self.on_account_refreshed(quota))
        
        thread = threading.Thread(target=query, daemon=True)
        thread.start()
    
    def on_account_refreshed(self, quota):
        """账户配额刷新完成"""
        if "error" in quota:
            # 不弹窗，只在状态栏显示
            self.status_var.set(f"刷新失败: {quota['error']}")
            return
        
        self.update_account_display(quota)
        self.status_var.set("账户配额已刷新")
    
    def update_account_display(self, account_quota):
        """更新账户配额显示"""
        limit = account_quota.get("limit", "-")
        used = account_quota.get("used", "-")
        remaining = account_quota.get("remaining", "-")
        
        if limit and used is not None:
            usage_pct = (used / limit) * 100
            usage_str = f"{usage_pct:.0f}%"
        else:
            usage_str = "-"
        
        # 更新表格
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)
        self.account_tree.insert("", tk.END, values=(limit, used, remaining, usage_str))
    
    def refresh_model_list(self):
        """刷新模型列表显示"""
        # 清除现有数据
        for item in self.model_tree.get_children():
            self.model_tree.delete(item)
        
        # 重新填充
        for model_id, quota in self.models:
            if quota is None:
                # 未查询过的模型
                values = (model_id, "-", "-", "-", "-")
            elif "error" in quota:
                values = (model_id, "错误", "-", "-", "-")
            else:
                model_info = quota.get("model", {})
                limit = model_info.get("limit", "-")
                used = model_info.get("used", "-")
                remaining = model_info.get("remaining", "-")
                
                if limit and used is not None:
                    usage_pct = (used / limit) * 100
                    usage_str = f"{usage_pct:.0f}%"
                else:
                    usage_str = "-"
                
                values = (model_id, limit, used, remaining, usage_str)
            
            self.model_tree.insert("", tk.END, values=values)


# ==================== 主程序 ====================
def main():
    root = tk.Tk()
    app = QuotaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()