import os
import re

class FileUtils:
    @staticmethod
    def is_archive(filename):
        """检查是否是支持的压缩格式，包括分卷文件"""
        filename = filename.lower()
        # 基础后缀
        if filename.endswith(('.rar', '.zip', '.7z')):
            return True
        
        # 分卷格式识别
        # .7z.001, .zip.001, .rar.001 等
        if re.search(r'\.(7z|zip|rar)\.\d{2,3}$', filename):
            return True
        # .part1.rar, .part01.rar
        if re.search(r'\.part\d+\.rar$', filename):
            return True
        # .r00, .r01 ...
        if re.search(r'\.r\d{2}$', filename):
            return True
        # .z01, .z02 ...
        if re.search(r'\.z\d{2}$', filename):
            return True
            
        return False

    @staticmethod
    def get_first_volume(path):
        """
        如果给定的是分卷文件，尝试找到它的第一卷。
        """
        filename = path.lower()
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)

        # 1. 处理 .7z.001, .zip.001 等
        match = re.search(r'^(.*)\.(7z|zip|rar)\.(\d+)$', basename, re.IGNORECASE)
        if match:
            prefix, ext, num = match.groups()
            # 对于 7z 分卷，第一卷是 .7z 文件本身；对于 zip/rar 分卷，第一卷是 .XXX.001
            if ext == '7z':
                first_vol_name = f"{prefix}.{ext}"
            else:
                first_vol_name = f"{prefix}.{ext}.001"
            first_vol_path = os.path.join(dirname, first_vol_name)
            if os.path.exists(first_vol_path):
                return first_vol_path

        # 2. 处理 .partN.rar
        match = re.search(r'^(.*)\.part(\d+)\.rar$', basename, re.IGNORECASE)
        if match:
            prefix, num = match.groups()
            # 可能是 .part1.rar 或 .part01.rar
            for fmt in ["part1.rar", "part01.rar", "part001.rar"]:
                first_vol_name = f"{prefix}.{fmt}"
                first_vol_path = os.path.join(dirname, first_vol_name)
                if os.path.exists(first_vol_path):
                    return first_vol_path

        # 3. 处理 .rNN 或 .zNN (第一卷通常是 .rar 或 .zip)
        if re.search(r'\.[rz]\d{2}$', basename, re.IGNORECASE):
            prefix = os.path.splitext(basename)[0]
            for ext in [".rar", ".zip"]:
                first_vol_path = os.path.join(dirname, prefix + ext)
                if os.path.exists(first_vol_path):
                    return first_vol_path

        return path

    @staticmethod
    def validate_path(path):
        return os.path.exists(path)

    @staticmethod
    def get_volume_files(base_path):
        """
        获取分卷文件序列中的所有文件
        支持格式: .7z.001, .7z.002, ... 或 .001, .002, ...
        """
        import glob
        import re
        
        path = base_path.lower()
        dirname = os.path.dirname(base_path)
        basename = os.path.basename(base_path)
        
        # 处理 .7z.001, .zip.001, .rar.001 格式
        match = re.search(r'^(.*)\.(7z|zip|rar)\.(\d+)$', basename, re.IGNORECASE)
        if match:
            prefix, ext, num = match.groups()
            pattern = os.path.join(dirname, f"{prefix}.{ext}.*")
            files = glob.glob(pattern)
            # 过滤出符合数字格式的文件
            volume_files = []
            for f in files:
                fname = os.path.basename(f).lower()
                if re.match(rf'^{prefix}\.{ext}\.\d+$', fname, re.IGNORECASE):
                    volume_files.append(f)
            # 按数字排序
            volume_files.sort(key=lambda x: int(re.search(r'\.(\d+)$', x).group(1)))
            return volume_files
        
        # 处理 .001, .002 格式 (无扩展名前缀)
        match = re.search(r'^(.*)\.(\d+)$', basename, re.IGNORECASE)
        if match:
            prefix, num = match.groups()
            # 检查是否有对应的主文件 (如 .7z, .zip, .rar)
            main_extensions = ['.7z', '.zip', '.rar']
            main_file = None
            for ext in main_extensions:
                candidate = os.path.join(dirname, prefix + ext)
                if os.path.exists(candidate):
                    main_file = candidate
                    break
            
            if main_file:
                # 如果有主文件，说明这是标准分卷格式
                pattern = os.path.join(dirname, f"{prefix}.*")
                files = glob.glob(pattern)
                volume_files = []
                for f in files:
                    fname = os.path.basename(f).lower()
                    if fname == os.path.basename(main_file).lower() or re.match(rf'^{prefix}\.\d+$', fname, re.IGNORECASE):
                        volume_files.append(f)
                # 排序：主文件在前，然后按数字排序
                def sort_key(x):
                    fname = os.path.basename(x).lower()
                    if fname == os.path.basename(main_file).lower():
                        return -1
                    else:
                        return int(re.search(r'\.(\d+)$', x).group(1))
                volume_files.sort(key=sort_key)
                return volume_files
        
        # 处理 .partN.rar 格式
        match = re.search(r'^(.*)\.part(\d+)\.rar$', basename, re.IGNORECASE)
        if match:
            prefix, num = match.groups()
            pattern = os.path.join(dirname, f"{prefix}.part*.rar")
            files = glob.glob(pattern)
            # 按数字排序
            files.sort(key=lambda x: int(re.search(r'part(\d+)\.rar$', x, re.IGNORECASE).group(1)))
            return files
        
        # 处理 .rNN, .zNN 格式
        match = re.search(r'^(.*)\.[rz](\d{2})$', basename, re.IGNORECASE)
        if match:
            prefix, num = match.groups()
            # 找到主文件 (.rar 或 .zip)
            main_ext = '.rar' if basename.endswith('.r' + num) else '.zip'
            main_file = os.path.join(dirname, prefix + main_ext)
            if os.path.exists(main_file):
                # 获取所有分卷
                pattern_r = os.path.join(dirname, f"{prefix}.r??")
                pattern_z = os.path.join(dirname, f"{prefix}.z??")
                files = glob.glob(pattern_r) + glob.glob(pattern_z)
                if os.path.exists(main_file):
                    files.append(main_file)
                # 排序：主文件在前，然后按数字排序
                def sort_key(x):
                    fname = os.path.basename(x).lower()
                    if fname == os.path.basename(main_file).lower():
                        return -1
                    elif fname.endswith('.r00') or fname.endswith('.z01'):
                        return 0
                    else:
                        return int(re.search(r'[rz](\d{2})$', x).group(1))
                files.sort(key=sort_key)
                return files
        
        return [base_path]

    @staticmethod
    def concatenate_volume_files(volume_files, temp_dir=None):
        """
        将分卷文件拼接成一个完整的临时文件
        返回临时文件路径
        """
        import tempfile
        import shutil
        
        if len(volume_files) <= 1:
            return volume_files[0]
        
        # 创建临时文件
        if temp_dir is None:
            temp_dir = tempfile.gettempdir()
        
        # 使用第一个文件的名称作为基础
        first_file = volume_files[0]
        base_name = os.path.basename(first_file)
        # 移除分卷后缀
        if re.search(r'\.(7z|zip|rar)\.\d+$', base_name, re.IGNORECASE):
            clean_name = re.sub(r'\.(7z|zip|rar)\.\d+$', r'.\1', base_name, flags=re.IGNORECASE)
        elif re.search(r'\.part\d+\.rar$', base_name, re.IGNORECASE):
            clean_name = re.sub(r'\.part\d+\.rar$', '.rar', base_name, flags=re.IGNORECASE)
        elif re.search(r'\.[rz]\d{2}$', base_name, re.IGNORECASE):
            clean_name = re.sub(r'\.[rz]\d{2}$', '.rar', base_name, flags=re.IGNORECASE)
        elif re.search(r'\.\d+$', base_name, re.IGNORECASE):
            # .001, .002 格式，需要确定主扩展名
            clean_name = base_name
            # 尝试从其他文件推断扩展名
            for f in volume_files:
                fname = os.path.basename(f)
                if '.' in fname and not fname.split('.')[-1].isdigit():
                    clean_name = fname
                    break
        else:
            clean_name = base_name
        
        temp_path = os.path.join(temp_dir, f"concatenated_{clean_name}")
        
        # 拼接文件
        with open(temp_path, 'wb') as outfile:
            for vol_file in volume_files:
                if os.path.exists(vol_file):
                    with open(vol_file, 'rb') as infile:
                        shutil.copyfileobj(infile, outfile)
        
        return temp_path

    @staticmethod
    def get_default_destination(archive_path):
        """获取默认解压目录（同名文件夹）"""
        dir_name = os.path.dirname(archive_path)
        base_name = os.path.basename(archive_path)
        # 移除后缀
        folder_name = re.sub(r'\.(rar|zip|7z|part\d+\.rar|7z\.\d{2,3}|zip\.\d{2,3}|rar\.\d{2,3}|r\d+|z\d+)$', '', base_name, flags=re.IGNORECASE)
        return os.path.join(dir_name, folder_name)
