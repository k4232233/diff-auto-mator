"""
@Author：haoran.xu
常量定义文件
"""

import sys
from pathlib import Path

def resource_path(relative_path):
    """获取资源文件的绝对路径，用于PyInstaller打包后的程序"""
    try:
        # PyInstaller 创建一个临时文件夹，并将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except Exception:
        base_path = Path(__file__).parent
    return str(Path(base_path) / relative_path)

# 默认路径常量
DEFAULT_OUTPUT_DIR = r"./ExtractedDiffs"
DEFAULT_DECOMPILER_PATH = resource_path("tools/cfr-0.152.jar")
FILE_LIST_TO_EXTRACT = r"./file_list_to_extract.txt"
DEFAULT_FILE = resource_path("tools/Untitled")

# WinMerge相关常量
WINMERGE_PATH = Path("C:/Program Files/WinMerge/WinMergeU.exe")
TARGET_DIR = Path("./merge_files")
HTML_REPORT_FILENAME = "merge_report.html"

# 提取文件路径相关常量
EXTRACTION_REPORT_FILENAME = "extracted_diff_data.txt"

# 文件扩展名相关常量
JAR_FILE_EXTENSION = '.jar'
CLASS_FILE_EXTENSION = '.class'

# Excel和PNG缓存目录常量
EXCEL_DIR = "./excel_files"
PNG_CACHE_DIR = "./png_cache"