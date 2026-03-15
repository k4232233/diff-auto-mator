# """
# @Author：haoran.xu
# """
# import subprocess
# import sys
# import os
# from pathlib import Path
#
# # 定义 PowerShell 脚本的路径 (假设和此 Python 脚本在同一目录，或者您提供绝对路径)
# POWERSHELL_SCRIPT_PATH = "ExtractJarFiles_final.ps1"
# LEFT_JAR_PATH = Path("C:/Users/haoran.xu/Desktop/diff/old/diff_test/athena-graphql-1.14.1.0.jar")
# RIGHT_JAR_PATH = Path("C:/Users/haoran.xu/Desktop/diff/old/diff_test/athena-graphql-1.14.4.0.jar")
# FILE_LIST_PATH = Path("C:/PythonWorkSpace/diff_test/filter/file_list_to_extract.txt")
#
#
# def run_powershell_script(left_jar, right_jar, file_list, output_dir="C:\\Temp\\ExtractedDiffs",
#                           decompiler_path="C:\\Tools\\cfr-0.152.jar"):
#     """使用 PowerShell.exe 调用您的 .ps1 脚本。"""
#
#     # 检查脚本是否存在
#     if not os.path.exists(POWERSHELL_SCRIPT_PATH):
#         print(f"错误: 找不到 PowerShell 脚本: {POWERSHELL_SCRIPT_PATH}")
#         sys.exit(1)
#
#     # 构建完整的 PowerShell 命令
#     # -ExecutionPolicy Bypass 允许脚本运行
#     # -File 指定要运行的脚本文件
#     # 后面是脚本的参数，使用'-ParameterName' 'Value'格式
#     command = [
#         "powershell.exe",
#         "-NoProfile",
#         "-ExecutionPolicy", "Bypass",
#         "-File", str(POWERSHELL_SCRIPT_PATH),
#         "-LeftJarPath", str(left_jar),
#         "-RightJarPath", str(right_jar),
#         "-FileListPath", str(file_list),
#     ]
#
#     print("正在执行 PowerShell 脚本...")
#     print(f"命令: {' '.join(command)}")
#
#     try:
#         # 执行命令并等待完成
#         result = subprocess.run(command, check=True, capture_output=False, text=True)
#
#         # 脚本成功执行后，返回码为 0
#         if result.returncode == 0:
#             print("\n✅ PowerShell 脚本执行成功。")
#         else:
#             # 如果 PowerShell 内部出现错误 (例如 exit 1)，returncode 会是 1
#             print(f"\n❌ PowerShell 脚本执行失败，返回码: {result.returncode}")
#             # 注意: 错误信息通常会直接输出到控制台，因为 capture_output=False
#
#     except subprocess.CalledProcessError as e:
#         # 仅当命令本身无法执行时 (如找不到 powershell.exe)
#         print(f"\n❌ 执行 powershell.exe 时发生错误: {e}")
#     except FileNotFoundError:
#         print("\n❌ 错误: 找不到 powershell.exe。请检查您的系统环境。")
#
#
# if __name__ == "__main__":
#     run_powershell_script(LEFT_JAR_PATH, RIGHT_JAR_PATH, FILE_LIST_PATH)
# --- 无用代码
