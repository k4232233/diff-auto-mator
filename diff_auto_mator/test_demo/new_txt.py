"""
@Author：haoran.xu
"""
import os
from pathlib import Path

# 修正路径，确保从项目根目录开始查找

DEFAULT_OUTPUT_DIR = Path("../ExtractedDiffs")  # 从test_demo目录回到上一级

if __name__ == '__main__':

    extracted_diffs_dir = DEFAULT_OUTPUT_DIR

    if extracted_diffs_dir.exists():

        # 查找最新的Extracted_File_Paths_xxx_xxx.txt文件

        extracted_path_files = list(extracted_diffs_dir.glob("Extracted_File_Paths_*.txt"))

        if extracted_path_files:
            latest_extracted_file = max(extracted_path_files, key=os.path.getctime)

            print(f"找到最新的提取文件路径: {latest_extracted_file}")

    else:

        print(f"目录不存在: {extracted_diffs_dir}")
