"""
@Author：haoran.xu
"""
import os

import sys

import zipfile

import subprocess

import shutil

from pathlib import Path

from datetime import datetime


from constants import DEFAULT_OUTPUT_DIR, DEFAULT_DECOMPILER_PATH, FILE_LIST_TO_EXTRACT


def extract_entry(jar_instance: zipfile.ZipFile, entry_path: str, output_base_dir: Path) -> Path or None:
    """
    从 JAR/ZIP 文件实例中提取单个条目。
    此函数不再自行打开/关闭 JAR 文件，从而避免了重复的 I/O 开销。
    """
    zip_entry_path = entry_path.replace("\\", "/")

    try:
        if zip_entry_path in jar_instance.namelist():
            destination_path = output_base_dir / entry_path

            destination_path.parent.mkdir(parents=True, exist_ok=True)

            jar_instance.extract(zip_entry_path, path=output_base_dir)

            final_extracted_path = output_base_dir / zip_entry_path

            print(f"  ✅ 提取成功: {entry_path}")
            return final_extracted_path
        else:
            jar_filename = Path(jar_instance.filename).name
            print(f"  ⚠️ 警告: 文件 {entry_path} 在 {jar_filename} 中找不到。跳过。")
            return None
    except Exception as e:
        print(f"提取 {entry_path} 时发生错误: {e}", file=sys.stderr)
        return None


def invoke_jar_decompiler(class_path: Path, decompiler_path: Path) -> bool:
    """将 .class 文件反编译成源代码，并用源代码覆盖原文件。"""
    print("-> 正在尝试反编译 .class 文件并替换内容 ...", end="")

    arguments = [
        "java",
        "-jar", str(decompiler_path),
        "--comments", "false",
        "--showversion", "false",
        str(class_path)
    ]

    try:
        if sys.platform.startswith('win'):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            result = subprocess.run(
                arguments,
                capture_output=True,
                text=True,
                encoding='utf-8',
                check=True,
                startupinfo=startupinfo
            )
        else:
            result = subprocess.run(
                arguments,
                capture_output=True,
                text=True,
                encoding='utf-8',
                check=True
            )

        source_code_content = result.stdout.strip()

        if source_code_content and len(source_code_content) > 100:

            with open(class_path, 'w', encoding='utf-8') as f:
                f.write(source_code_content)

            print(f"  📝 .class 文件内容已成功替换为源代码。 ")
            return True
        else:
            print(f"反编译失败：未捕获到足够的源代码。")
            print(f"  请检查 Decompiler ({decompiler_path.name}) 是否能处理 {class_path.name}。", file=sys.stderr)
            return False

    except subprocess.CalledProcessError as e:
        print(f"反编译命令执行失败: {e.stderr}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"执行反编译或写入文件时发生错误: {e}", file=sys.stderr)
        return False


def extract_jar_diffs(
        left_jar_path: str,
        right_jar_path: str,
        file_list_path: str = FILE_LIST_TO_EXTRACT,
        target_output_dir: str = DEFAULT_OUTPUT_DIR,
        decompiler_path: str = DEFAULT_DECOMPILER_PATH
) -> dict:
    """
    根据文件列表，从两个 JAR 文件中提取指定文件，并可选择将 .class
    文件替换为反编译后的源代码。

    Args:
        left_jar_path: 左侧 (旧) JAR 文件的完整路径。
        right_jar_path: 右侧 (新) JAR 文件的完整路径。
        file_list_path: 包含要提取文件列表的文本文件路径。
        target_output_dir: 目标输出目录。默认为 C:\\Temp\\ExtractedDiffs。
        decompiler_path: Java 反编译器 JAR 文件的完整路径。默认为 C:\\Tools\\cfr-0.152.jar。

    Returns:
        返回一个字典，包含提取文件的 V1 和 V2 目录路径。
    """

    p_file_list = Path(file_list_path)
    p_left_jar = Path(left_jar_path)
    p_right_jar = Path(right_jar_path)
    p_output_dir = Path(target_output_dir)

    p_decompiler = Path(decompiler_path) if decompiler_path else None

    required_files = {
        "文件列表": p_file_list,
        "左侧 JAR": p_left_jar,
        "右侧 JAR": p_right_jar,
    }

    for name, path in required_files.items():
        if not path.exists():
            print(f"错误: 找不到 {name} 文件: {path}", file=sys.stderr)
            return {"error": f"Missing file: {path}"}

    is_decompiler_available = False
    if p_decompiler and p_decompiler.exists():
        is_decompiler_available = True

    default_decompiler_path_obj = Path(DEFAULT_DECOMPILER_PATH)

    if p_decompiler and not is_decompiler_available and p_decompiler != default_decompiler_path_obj:
        print(f"错误: 找不到反编译器 JAR 文件: {p_decompiler}", file=sys.stderr)
        return {"error": f"Missing decompiler: {p_decompiler}"}

    if p_decompiler and not is_decompiler_available and p_decompiler == default_decompiler_path_obj:
        print(f"警告: 正在使用默认反编译器路径 ({p_decompiler})，但文件不存在。将跳过所有反编译。", file=sys.stderr)

    v1_output_dir = p_output_dir / f"V1_{p_left_jar.name}"
    v2_output_dir = p_output_dir / f"V2_{p_right_jar.name}"

    print(f"正在清理和创建 V1/V2 输出目录...")

    for dir_path in [v1_output_dir, v2_output_dir]:
        if dir_path.exists() and dir_path.is_dir():
            shutil.rmtree(dir_path)

        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  已创建目录: {dir_path}")

    try:
        with open(p_file_list, 'r', encoding='utf-8') as f:
            file_paths = [
                line.strip()
                for line in f
                if line.strip() and not line.strip().startswith('#')
            ]
    except Exception as e:
        print(f"读取文件列表时发生错误: {e}", file=sys.stderr)
        return {"error": f"Error reading file list: {e}"}

    if not file_paths:
        print("文件列表为空。操作结束。")
        return {"v1_dir": str(v1_output_dir), "v2_dir": str(v2_output_dir)}

    print(f"--- JAR 文件差异提取与内容替换工具 ---")
    print(f"正在读取文件列表: {p_file_list}")
    print(f"总共要处理 {len(file_paths)} 个文件条目。")

    v1_extracted_files = []
    v2_extracted_files = []

    try:
        with zipfile.ZipFile(p_left_jar, 'r') as jar_left, \
                zipfile.ZipFile(p_right_jar, 'r') as jar_right:

            for i, file_entry in enumerate(file_paths):
                print(f"\n=============================================")
                print(f"({i + 1}/{len(file_paths)}) 正在处理文件: {file_entry}")
                print(f"=============================================")

                print(f"-> 正在从 V1 文件 [{p_left_jar.name}] 中提取...")
                v1_extracted_path = extract_entry(jar_left, file_entry, v1_output_dir)

                print(f"-> 正在从 V2 文件 [{p_right_jar.name}] 中提取...")
                v2_extracted_path = extract_entry(jar_right, file_entry, v2_output_dir)

                if file_entry.endswith(".class"):

                    if is_decompiler_available:
                        if v1_extracted_path:
                            invoke_jar_decompiler(v1_extracted_path, p_decompiler)

                        if v2_extracted_path:
                            invoke_jar_decompiler(v2_extracted_path, p_decompiler)
                    else:
                        print("-> 跳过 .class 文件的反编译。未提供有效的反编译器路径或文件不存在。")

                if v1_extracted_path:
                    v1_extracted_files.append(str(v1_extracted_path.resolve()))
                if v2_extracted_path:
                    v2_extracted_files.append(str(v2_extracted_path.resolve()))

    except zipfile.BadZipFile:
        print("错误: 一个或两个 JAR 文件似乎不是有效的 ZIP 文件。", file=sys.stderr)
        return {"error": "Invalid JAR file format."}
    except Exception as e:
        print(f"处理 JAR 文件时发生意外错误: {e}", file=sys.stderr)
        return {"error": f"Unexpected error during JAR processing: {e}"}

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    path_summary_file = p_output_dir / f"Extracted_File_Paths_{timestamp}.txt"

    summary_content = [
        "==========================================================",
        "      JAR 差异提取与内容替换结果 - 文件路径列表",
        f"      运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "==========================================================",
        f"\n--- 旧版本 (V1): {p_left_jar.name} 文件路径 ---\n",
        *(f for f in v1_extracted_files if f),
        f"\n--- 新版本 (V2): {p_right_jar.name} 文件路径 ---\n",
        *(f for f in v2_extracted_files if f),
    ]

    try:
        with open(path_summary_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary_content))

        print("\n-----------------------------------------------------")
        print("📁 提取文件的绝对路径已记录到以下文件：")
        print(f"   {path_summary_file}")
        print("-----------------------------------------------------")

    except Exception as e:
        print(f"写入摘要文件时发生错误: {e}", file=sys.stderr)

    print("🎉 提取完成！所有指定的文件已成功提取到以下目录：")
    print(f"旧版本 (V1) 输出目录: {v1_output_dir}")
    print(f"新版本 (V2) 输出目录: {v2_output_dir}")
    print("-----------------------------------------------------")
    print("您可以将这两个目录导入到文件对比工具 (如 Beyond Compare, WinMerge) 中进行差异分析。")
    print("请注意，.class 文件现在包含人类可读的源代码文本。")

    return {
        "v1_dir": str(v1_output_dir),
        "v2_dir": str(v2_output_dir),
        "summary_file": str(path_summary_file)
    }


# =========================================================
# 示例用法 (供用户替换为实际路径)
# =========================================================

# if __name__ == '__main__':
#
#     # 现在改为交互式输入，无需编辑代码即可使用！
#     print("\n--- JAR 差异提取工具 - 请输入路径 ---")
#     print("提示：复制 Windows 路径时，脚本会自动处理首尾的空格和双引号 (若有)。")
#
#     try:
#         # 1. 获取左侧 JAR 路径
#         left_jar_input = input("1. 请输入左侧 (旧) JAR 文件的完整路径: ").strip().strip('"')
#         LEFT_JAR = left_jar_input
#
#         # 2. 获取右侧 JAR 路径
#         right_jar_input = input("2. 请输入右侧 (新) JAR 文件的完整路径: ").strip().strip('"')
#         RIGHT_JAR = right_jar_input
#
#         # # 3. 获取文件列表路径
#         # file_list_input = input("3. 请输入文件列表文件的完整路径: ").strip().strip('"')
#         # FILE_LIST = file_list_input
#
#         # # 4. 获取可选的输出目录 (留空则使用默认值)
#         # output_dir_input = input(f"4. 请输入输出目录 (默认为 {DEFAULT_OUTPUT_DIR}): ").strip().strip('"')
#         # OUTPUT_DIR = output_dir_input if output_dir_input else DEFAULT_OUTPUT_DIR
#
#         # # 5. 获取可选的反编译器路径 (留空则使用默认值)
#         # decompiler_input = input(f"5. 请输入反编译器 JAR 路径 (默认为 {DEFAULT_DECOMPILER_PATH}): ").strip().strip('"')
#         # DECOMPILER = decompiler_input if decompiler_input else DEFAULT_DECOMPILER_PATH
#
#         print("\n--- 正在运行 JAR 差异提取 ---")
#
#         results = extract_jar_diffs(
#             left_jar_path=LEFT_JAR,
#             right_jar_path=RIGHT_JAR,
#             file_list_path=FILE_LIST_TO_EXTRACT,
#             target_output_dir=DEFAULT_OUTPUT_DIR,
#             decompiler_path=DEFAULT_DECOMPILER_PATH
#         )
#
#         if "error" not in results:
#             print(f"\n操作结果目录：\nV1: {results['v1_dir']}\nV2: {results['v2_dir']}")
#         else:
#             print(f"\n操作失败: {results['error']}")
#
#     except Exception as e:
#         print(f"\n脚本执行发生致命错误: {e}", file=sys.stderr)