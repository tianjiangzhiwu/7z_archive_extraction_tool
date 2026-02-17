import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

# 注意：tkinterdnd2 需要单独安装: pip install tkinterdnd2
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("Warning: tkinterdnd2 not installed. Drag and drop disabled.")

from .password_book_gui import PasswordBookGUI
from utils.file_utils import FileUtils

class MainWindow:
    def __init__(self, root, config, extractor_engine, password_manager):
        self.root = root
        self.config = config
        self.engine = extractor_engine
        self.pwd_manager = password_manager
        
        # 初始化密码本路径
        passwords_file = self.config.get("passwords_file")
        if passwords_file and os.path.exists(passwords_file):
            self.pwd_manager.set_passwords_file(passwords_file)
        
        self.root.title("Python WinRAR 解压工具")
        self.root.geometry("600x500")
        
        self._setup_ui()
        self._setup_dnd()

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 文件选择
        file_frame = ttk.LabelFrame(main_frame, text="压缩文件", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(file_frame, text="浏览", command=self.browse_file)
        browse_btn.pack(side=tk.RIGHT)

        # 拖拽提示区
        self.drop_label = tk.Label(
            main_frame,
            text="拖拽压缩文件到此处自动解压",
            relief="groove",
            borderwidth=2,
            height=5,
            bg="#f0f0f0"
        )
        self.drop_label.pack(fill=tk.X, pady=10)

        # 状态显示
        self.status_var = tk.StringVar(value="准备就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("Segoe UI", 10))
        status_label.pack(pady=5)

        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=10)

        # 日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="解压日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # 创建文本框和滚动条
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_text_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        log_scrollbar = ttk.Scrollbar(log_text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scrollbar.set)

        # 底部控制
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.extract_btn = ttk.Button(control_frame, text="开始解压", command=self.start_extraction)
        self.extract_btn.pack(side=tk.LEFT, padx=5)
        
        # 密码本路径选择
        pwd_path_btn = ttk.Button(control_frame, text="选择密码本", command=self.select_passwords_file)
        pwd_path_btn.pack(side=tk.LEFT, padx=5)
        
        pwd_book_btn = ttk.Button(control_frame, text="密码本管理", command=self.open_password_book)
        pwd_book_btn.pack(side=tk.RIGHT, padx=5)

    def _setup_dnd(self):
        if HAS_DND:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.handle_drop)
            self.drop_label.config(text="拖拽文件到此处自动开始 (支持 DND)")
        else:
            self.drop_label.config(text="请安装 tkinterdnd2 以支持拖拽")

    def handle_drop(self, event):
        # 提取路径，处理可能包含 {} 的 Windows 路径
        path = event.data
        if path.startswith('{') and path.endswith('}'):
            path = path[1:-1]
        
        if FileUtils.is_archive(path):
            # 识别并获取第一卷
            first_volume = FileUtils.get_first_volume(path)
            self.file_path_var.set(first_volume)
            
            if first_volume != path:
                self.status_var.set(f"已自动识别分卷主文件: {os.path.basename(first_volume)}")
            
            # 自动开始
            self.start_extraction()
        else:
            messagebox.showwarning("格式不支持", "请拖拽有效的压缩文件 (.rar, .zip, .7z, .001, .part1等)")

    def browse_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("压缩文件", "*.rar *.zip *.7z"), ("所有文件", "*.*")]
        )
        if path:
            self.file_path_var.set(path)

    def start_extraction(self):
        path = self.file_path_var.get()
        if not path or not os.path.exists(path):
            messagebox.showwarning("错误", "请选择有效的文件")
            return

        dest = FileUtils.get_default_destination(path)
        
        self.extract_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
        self.progress.config(mode='determinate')
        self.status_var.set("正在解压中，请稍候...")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, f"开始解压文件: {path}\n")
        self.log_text.insert(tk.END, f"目标目录: {dest}\n")
        self.log_text.config(state=tk.DISABLED)
        
        # 开启线程避免界面卡死
        thread = threading.Thread(target=self.run_extraction, args=(path, dest))
        thread.daemon = True
        thread.start()

    def run_extraction(self, path, dest):
        def status_callback(event_type, message):
            """状态回调函数"""
            if event_type == "status":
                self.root.after(0, lambda: self.status_var.set(message))
            elif event_type == "log":
                self.root.after(0, lambda: self.update_log(message))
            elif event_type == "info":
                self.root.after(0, lambda: self.update_log(f"[INFO] {message}"))
            elif event_type == "error":
                self.root.after(0, lambda: self.update_log(f"[ERROR] {message}"))
            elif event_type == "progress":
                # 更新进度条
                try:
                    percent = int(message)
                    self.root.after(0, lambda p=percent: self.progress.config(value=p))
                except (ValueError, TypeError):
                    pass
        
        success, used_pwd = self.engine.extract_with_passwords(path, dest, status_callback)
        
        self.root.after(0, lambda: self.finish_extraction(success, used_pwd, dest))

    def finish_extraction(self, success, used_pwd, dest):
        self.progress['value'] = 100 if success else 0
        self.extract_btn.config(state=tk.NORMAL)
        
        if success:
            msg = f"解压成功！\n保存至: {dest}"
            if used_pwd:
                msg += f"\n使用密码: {used_pwd}"
            else:
                msg += "\n(无密码解压)"
            self.status_var.set("解压完成")
            messagebox.showinfo("成功", msg)
        else:
            self.status_var.set("解压失败")
            messagebox.showerror("失败", "解压失败。可能是密码不正确或文件已损坏。")

    def open_password_book(self):
        PasswordBookGUI(self.root, self.pwd_manager)

    def update_log(self, message):
        """更新日志显示区域"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)  # 自动滚动到最新消息
        self.log_text.config(state=tk.DISABLED)
    
    def select_passwords_file(self):
        """选择密码本文件"""
        path = filedialog.askopenfilename(
            title="选择密码本文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if path:
            self.pwd_manager.set_passwords_file(path)
            self.config.set("passwords_file", path)
            password_count = len(self.pwd_manager.get_all_passwords())
            self.status_var.set(f"已加载 {password_count} 个密码")
            self.update_log(f"密码本已加载: {path}")
            self.update_log(f"包含 {password_count} 个密码")
