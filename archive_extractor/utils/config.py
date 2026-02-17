import os
import sys
import winreg
import json

class Config:
    def __init__(self, config_file="config.json"):
        # 获取正确的基础目录（支持PyInstaller打包）
        base_dir = self._get_base_dir()
        
        # 如果config_file是相对路径，尝试在基础目录下查找
        if not os.path.isabs(config_file):
            config_file = os.path.join(base_dir, config_file)
            
        self.config_file = config_file
        self.default_config = {
            "sevenzip_path": self._find_sevenzip_path(),
            "last_extract_path": "",
            "passwords_file": "",
            "auto_extract": True
        }
        self.config = self.load_config()

    def _find_sevenzip_path(self):
        """尝试从注册表查找 7-Zip 安装路径"""
        # 7-Zip 通常安装在以下位置
        common_paths = [
            r"D:\7-Zip\7z.exe",
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
            r"C:\7-Zip\7z.exe"
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
        return ""

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 补充缺失的默认字段
                    for k, v in self.default_config.items():
                        if k not in config:
                            config[k] = v
                    return config
            except Exception:
                return self.default_config
        return self.default_config

    def save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get(self, key):
        return self.config.get(key, self.default_config.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def _get_base_dir(self):
        """获取应用的基础目录，支持PyInstaller打包"""
        if getattr(sys, 'frozen', False):
            # 打包后的可执行文件
            return os.path.dirname(sys.executable)
        else:
            # 开发环境
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
config = Config()
