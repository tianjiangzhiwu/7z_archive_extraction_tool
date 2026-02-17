import os
import json
from datetime import datetime

class SimplePasswordManager:
    def __init__(self, passwords_file=None):
        """初始化密码管理器
        Args:
            passwords_file: 密码文件路径，如果为None则使用默认路径
        """
        self.passwords_file = passwords_file
        self.passwords = []
        if self.passwords_file and os.path.exists(self.passwords_file):
            self.load_passwords()
    
    def load_passwords(self):
        """从.txt文件加载密码，每行一个密码"""
        if not self.passwords_file or not os.path.exists(self.passwords_file):
            self.passwords = []
            return
        
        try:
            with open(self.passwords_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 去除空白字符和空行
                self.passwords = [line.strip() for line in lines if line.strip()]
        except Exception:
            self.passwords = []
    
    def save_passwords(self):
        """保存密码到.txt文件，每行一个密码"""
        if not self.passwords_file:
            return
        
        try:
            # 确保目录存在
            directory = os.path.dirname(self.passwords_file)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            with open(self.passwords_file, 'w', encoding='utf-8') as f:
                for password in self.passwords:
                    f.write(password + '\n')
        except Exception:
            pass
    
    def add_password(self, password):
        """添加密码"""
        if not password:
            return False
        if password not in self.passwords:
            self.passwords.append(password)
            self.save_passwords()
            return True
        return False
    
    def remove_password(self, password):
        """移除密码"""
        if password in self.passwords:
            self.passwords.remove(password)
            self.save_passwords()
            return True
        return False
    
    def get_all_passwords(self):
        """获取所有密码"""
        return self.passwords.copy()
    
    def set_passwords_file(self, file_path):
        """设置密码文件路径"""
        self.passwords_file = file_path
        if file_path and os.path.exists(file_path):
            self.load_passwords()
        else:
            self.passwords = []