import json
import os
import sys
from datetime import datetime

class PasswordManager:
    def __init__(self, storage_path="data/passwords.json"):
        # 获取正确的基础目录（支持PyInstaller打包）
        if not os.path.isabs(storage_path):
            base_dir = self._get_base_dir()
            storage_path = os.path.join(base_dir, storage_path)
        self.storage_path = storage_path
        self.passwords = []
        self._ensure_data_dir()
        self.load_passwords()

    def _ensure_data_dir(self):
        directory = os.path.dirname(self.storage_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

    def load_passwords(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.passwords = data.get("passwords", [])
            except (json.JSONDecodeError, Exception):
                self.passwords = []
        else:
            self.passwords = []
        return self.passwords

    def save_passwords(self):
        data = {
            "passwords": self.passwords,
            "last_updated": datetime.now().isoformat()
        }
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def add_password(self, password):
        if not password:
            return False
        if password not in self.passwords:
            self.passwords.append(password)
            self.save_passwords()
            return True
        return False
    
    def _get_base_dir(self):
        """获取应用的基础目录，支持PyInstaller打包"""
        if getattr(sys, 'frozen', False):
            # 打包后的可执行文件
            if hasattr(sys, '_MEIPASS'):
                # --onefile 模式：数据文件在 _MEIPASS 目录中
                return sys._MEIPASS
            else:
                # --onedir 模式：数据文件在 _internal 目录中
                internal_dir = os.path.join(os.path.dirname(sys.executable), "_internal")
                if os.path.exists(internal_dir):
                    return internal_dir
                else:
                    # 备用：直接在可执行文件目录中查找
                    return os.path.dirname(sys.executable)
        else:
            # 开发环境
            current_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.dirname(os.path.dirname(current_dir))

    def remove_password(self, password):
        if password in self.passwords:
            self.passwords.remove(password)
            self.save_passwords()
            return True
        return False

    def get_all_passwords(self):
        return self.passwords

    def deduplicate(self):
        original_count = len(self.passwords)
        # 保持顺序去重
        seen = set()
        self.passwords = [x for x in self.passwords if not (x in seen or seen.add(x))]
        if len(self.passwords) != original_count:
            self.save_passwords()
            return True
        return False
