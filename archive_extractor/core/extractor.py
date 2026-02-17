from core.sevenzip_handler import SevenZipHandler
from core.password_manager import PasswordManager
from utils.file_utils import FileUtils
import os

class ExtractorEngine:
    def __init__(self, sevenzip_path, password_manager: PasswordManager):
        self.handler = SevenZipHandler(sevenzip_path)
        self.password_manager = password_manager



    def extract_with_passwords(self, archive_path, destination, status_callback=None):
        """核心解压逻辑：先尝试无密码，再尝试密码本"""
        
        # 对于分卷文件，7z会自动处理，无需拼接
        # 直接使用原始路径
        
        try:
            # 直接尝试解压流程，避免耗时的加密检测
            log_message = f"开始解压流程: {archive_path}"
            print(log_message)
            if status_callback:
                status_callback("status", "开始解压流程...")
                status_callback("log", log_message)
            
            # 1. 首先尝试无密码解压
            log_message = f"正在尝试无密码解压: {archive_path}"
            print(log_message)
            if status_callback:
                status_callback("status", "正在尝试无密码解压...")
                status_callback("log", log_message)
            if self.handler.extract(archive_path, destination, password=None, progress_callback=lambda p: status_callback("progress", p) if status_callback else None):
                return True, None

            # 2. 如果无密码失败，尝试密码本中的所有密码
            passwords = self.password_manager.get_all_passwords()
            log_message = f"无密码解压失败，正在尝试密码本中的 {len(passwords)} 个密码: {archive_path}"
            print(log_message)
            if status_callback:
                status_callback("status", f"尝试密码本 ({len(passwords)} 个密码)...")
                status_callback("log", log_message)
            
            for i, pwd in enumerate(passwords, 1):
                log_message = f"正在尝试第 {i}/{len(passwords)} 个密码: {pwd}"
                print(log_message)
                if status_callback:
                    status_callback("status", f"尝试密码 ({i}/{len(passwords)}): {pwd}")
                    status_callback("log", log_message)
                if self.handler.extract(archive_path, destination, password=pwd, progress_callback=lambda p: status_callback("progress", p) if status_callback else None):
                    return True, pwd

            # 3. 如果都失败，返回失败
            log_message = f"所有密码尝试失败，解压失败: {archive_path}"
            print(log_message)
            if status_callback:
                status_callback("status", "所有密码尝试失败")
                status_callback("log", log_message)
            return False, None
            
        except Exception as e:
            error_message = f"Error during extraction: {e}"
            print(error_message)
            if status_callback:
                status_callback("error", error_message)
            return False, None

    def extract_single_password(self, archive_path, destination, password):
        """使用指定密码解压"""
        # 对于分卷文件，7z会自动处理，无需拼接
        try:
            return self.handler.extract(archive_path, destination, password=password)
        except Exception as e:
            print(f"Error during single password extraction: {e}")
            return False
