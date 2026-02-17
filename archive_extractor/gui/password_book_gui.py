import tkinter as tk
from tkinter import ttk, messagebox

class PasswordBookGUI:
    def __init__(self, parent, password_manager):
        self.window = tk.Toplevel(parent)
        self.window.title("密码本管理")
        self.window.geometry("400x500")
        self.manager = password_manager
        
        self._setup_ui()
        self.refresh_list()

    def _setup_ui(self):
        frame = ttk.Frame(self.window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # 输入区域
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.pwd_entry = ttk.Entry(input_frame)
        self.pwd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        add_btn = ttk.Button(input_frame, text="添加密码", command=self.add_password)
        add_btn.pack(side=tk.RIGHT)

        # 列表区域
        self.listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE)
        self.listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        # 按钮区域
        btn_frame = ttk.Frame(self.window, padding="10")
        btn_frame.pack(fill=tk.X)
        
        del_btn = ttk.Button(btn_frame, text="删除选中", command=self.delete_selected)
        del_btn.pack(side=tk.LEFT, padx=5)
        
        dedup_btn = ttk.Button(btn_frame, text="去重", command=self.deduplicate)
        dedup_btn.pack(side=tk.LEFT, padx=5)
        
        close_btn = ttk.Button(btn_frame, text="关闭", command=self.window.destroy)
        close_btn.pack(side=tk.RIGHT, padx=5)

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for pwd in self.manager.get_all_passwords():
            self.listbox.insert(tk.END, pwd)

    def add_password(self):
        pwd = self.pwd_entry.get().strip()
        if pwd:
            if self.manager.add_password(pwd):
                self.refresh_list()
                self.pwd_entry.delete(0, tk.END)
            else:
                messagebox.showinfo("提示", "密码已存在")
        else:
            messagebox.showwarning("警告", "请输入密码")

    def delete_selected(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            return
        
        if messagebox.askyesno("确认", f"确定删除选中的 {len(selected_indices)} 个密码吗？"):
            # 倒序删除，避免索引变化
            passwords_to_remove = [self.listbox.get(i) for i in selected_indices]
            for pwd in passwords_to_remove:
                self.manager.remove_password(pwd)
            self.refresh_list()

    def deduplicate(self):
        if self.manager.deduplicate():
            self.refresh_list()
            messagebox.showinfo("提示", "已完成去重")
        else:
            messagebox.showinfo("提示", "无需去重")
