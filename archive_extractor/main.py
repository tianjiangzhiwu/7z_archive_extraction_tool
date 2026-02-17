import sys
import os
import tkinter as tk
from tkinter import messagebox

# 处理路径问题，确保可以从子目录导入
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config import config
from core.simple_password_manager import SimplePasswordManager
from core.extractor import ExtractorEngine
from gui.main_window import MainWindow

# 尝试导入 TkinterDnD
try:
    from tkinterdnd2 import TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

def main():
    # 初始化核心组件
    # 使用None作为初始密码文件路径，让用户在GUI中选择
    pwd_manager = SimplePasswordManager()
    engine = ExtractorEngine(config.get("sevenzip_path"), pwd_manager)

    # 检查 7-Zip
    if not engine.handler.check_sevenzip_installed():
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("错误", "未找到 7-Zip 安装路径，请检查系统或 config.json")
        root.destroy()
        return

    # 启动 GUI
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    
    app = MainWindow(root, config, engine, pwd_manager)
    root.mainloop()

if __name__ == "__main__":
    from tkinter import messagebox
    main()
