"""
@Author：haoran.xu
文件清理模块
用于清理生成的临时文件和报告
"""

import os
from pathlib import Path
from constants import TARGET_DIR, FILE_LIST_TO_EXTRACT


def cleanup_temp_files():
    """
    清理临时文件
    """
    print("\n--- 开始清理临时文件 ---")
    
    if TARGET_DIR.exists() and TARGET_DIR.is_dir():
        for item in TARGET_DIR.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                    print(f"已删除临时文件: {item}")
            except Exception as e:
                print(f"删除 {item} 时发生错误: {e}")
    else:
        print(f"目录不存在: {TARGET_DIR}")
    
    current_file_list_path = Path("file_list_to_extract.txt")
    if current_file_list_path.exists():
        try:
            current_file_list_path.write_text('', encoding='utf-8')
            print(f"已清空临时文件内容: {current_file_list_path}")
        except Exception as e:
            print(f"清空文件 {current_file_list_path} 时发生错误: {e}")
    
    print("--- 临时文件清理完成 ---\n")


if __name__ == "__main__":
    cleanup_temp_files()