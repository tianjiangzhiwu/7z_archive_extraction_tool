import subprocess
import os
import re

class SevenZipHandler:
    def __init__(self, sevenzip_path):
        self.sevenzip_path = sevenzip_path

    def check_sevenzip_installed(self):
        """检查7z是否已安装"""
        if not self.sevenzip_path:
            return False
        return os.path.exists(self.sevenzip_path)

    def extract(self, archive_path, destination, password=None, progress_callback=None):
        """
        使用 7z 命令行进行解压
        x: 解压完整路径
        -y: 假设所有查询都回答 '是'
        -o: 指定输出目录
        -p: 指定密码（无密码时不使用此参数）
        注意：移除了 -bd 参数以允许获取进度信息
        """
        if not self.check_sevenzip_installed():
            raise FileNotFoundError("7-Zip not found. Please check configuration.")

        # 确保目标目录存在
        if not os.path.exists(destination):
            os.makedirs(destination)

        # 构建命令
        command = [
            self.sevenzip_path,
            "x",
            "-y",
            f"-o{destination}",
            archive_path
        ]

        if password is not None:
            # 7z 命令行中 -p 和密码之间不能有空格
            command.insert(4, f"-p{password}")
        else:
            # 提供空密码以避免交互式提示
            command.insert(4, "-p")

        try:
            # 先尝试使用 subprocess.run 获取完整输出（用于日志）
            # 如果需要进度回调，再使用 Popen
            if progress_callback is None:
                # 简单模式：使用 run
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                # 输出日志到控制台
                if result.stdout:
                    print("7z output:", result.stdout)
                if result.stderr:
                    print("7z error:", result.stderr)
                return result.returncode == 0
            else:
                # 进度模式：使用 Popen
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                last_percent = 0
                import time
                start_time = time.time()
                timeout_seconds = 300  # 5分钟超时
                
                # 读取输出行
                for line in iter(process.stdout.readline, ''):
                    if time.time() - start_time > timeout_seconds:
                        print(f"Extraction timeout after {timeout_seconds} seconds")
                        process.terminate()
                        return False
                    
                    if line:
                        # 输出到控制台用于调试
                        print(f"7z: {line.strip()}")
                        # 尝试解析进度
                        percent = self._parse_progress(line)
                        if percent is not None and percent > last_percent:
                            last_percent = percent
                            progress_callback(percent)
                
                process.wait()
                return_code = process.returncode
                return return_code == 0
        except Exception as e:
            print(f"Extraction error: {e}")
            return False

    def _parse_progress(self, line):
        """从7z输出行中解析进度百分比"""
        import re
        # 匹配百分比模式，如 "50%" 或 "... 50%"
        percent_match = re.search(r'(\d+)%', line)
        if percent_match:
            try:
                percent = int(percent_match.group(1))
                if 0 <= percent <= 100:
                    return percent
            except ValueError:
                pass
        return None

    def test_archive(self, archive_path):
        """测试压缩包是否损坏或获取信息"""
        command = [self.sevenzip_path, "t", "-y", archive_path]
        try:
            result = subprocess.run(command, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return result.returncode == 0
        except Exception:
            return False

    def is_encrypted(self, archive_path):
        """检测压缩包是否加密"""
        # 首先检查文件是否存在
        if not os.path.exists(archive_path):
            print(f"Archive file does not exist: {archive_path}")
            return False
        
        # 使用7z l命令列出内容并检测加密状态
        command = [self.sevenzip_path, "l", "-y", archive_path]
        try:
            # 添加超时（60秒），避免大文件长时间阻塞
            result = subprocess.run(command, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=60)
            output = result.stdout.lower() + result.stderr.lower()
            
            # 检查7z输出中的加密标记
            encrypted_indicators = ['encrypted', 'password', '密', '密码', 'encryption', 'enter password', 'requires password']
            for indicator in encrypted_indicators:
                if indicator in output:
                    return True
            
            # 如果returncode为2，通常表示需要密码（即加密）
            if result.returncode == 2:
                return True
                
            # 对于分卷文件，7z会自动处理，我们只需要检测第一个分卷
            # 如果是分卷文件且返回码不为0，但输出包含加密指示符，视为加密
            archive_name = os.path.basename(archive_path).lower()
            volume_extensions = ['.part001.rar', '.part0001.rar', '.r00', '.r01', '.z01', '.z02', '.7z.001', '.7z.002']
            is_volume = any(archive_name.endswith(ext) for ext in volume_extensions)
            
            if is_volume and result.returncode != 0:
                if any(indicator in output for indicator in encrypted_indicators):
                    return True
            
            # 默认情况下，如果没有明确的加密指示，认为不是加密的
            return False
        except subprocess.TimeoutExpired:
            print(f"Encryption check timeout for: {archive_path}, assuming encrypted")
            # 超时情况下，保守地假设是加密的（因为大文件更可能是加密的）
            return True
        except Exception as e:
            print(f"Error while checking encryption for: {archive_path}, error: {e}")
            # 如果无法确定，保守地假设是加密的
            return True