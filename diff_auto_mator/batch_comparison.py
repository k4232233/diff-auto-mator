"""

@Author：haoran.xu

"""

import sys

import os

from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from winmerge_to_html import run_winmerge_comparison

from constants import DEFAULT_FILE


def generate_comparison_list(extracted_file_paths_file: Path):
    """
    从Extracted_File_Paths_xxx_xxx.txt文件中解析路径，组成比较对
    """
    print(f"--- 解析文件路径: {extracted_file_paths_file} ---")

    comparison_pairs = []

    with open(extracted_file_paths_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    v1_files = []
    v2_files = []

    current_section = None

    for line in lines:
        line = line.strip()

        if "旧版本 (V1)" in line:
            current_section = "V1"
        elif "新版本 (V2)" in line:
            current_section = "V2"
        elif line and not line.startswith("=") and not line.startswith("-") and not line.startswith("运行时间"):
            if current_section == "V1":
                v1_files.append(Path(line))
            elif current_section == "V2":
                v2_files.append(Path(line))

    v1_file_map = {path.name: path for path in v1_files}
    v2_file_map = {path.name: path for path in v2_files}

    all_filenames = set(v1_file_map.keys()) | set(v2_file_map.keys())

    for filename in all_filenames:
        v1_file = v1_file_map.get(filename)
        v2_file = v2_file_map.get(filename)

        is_jar_file = filename.lower().endswith('.jar')

        if is_jar_file:

            def extract_base_name(jar_name):
                name_part = jar_name[:-4]  # 去掉 .jar 扩展名
                parts = name_part.split('-')

                i = len(parts) - 1

                while i >= 0:
                    part = parts[i]

                    if any(c.isdigit() for c in part) and all(c.isdigit() or c == '.' for c in part):
                        i -= 1
                    else:
                        break

                if i >= 0:
                    non_version_parts = parts[:i + 1]
                    base_name = '-'.join(non_version_parts)
                    return base_name

                return name_part

            base_name_v1 = extract_base_name(v1_file.name) if v1_file else None
            base_name_v2 = extract_base_name(v2_file.name) if v2_file else None

            if v1_file and v2_file and base_name_v1 == base_name_v2:
                comparison_pairs.append((v1_file, v2_file))

        else:
            if v1_file and v2_file:
                comparison_pairs.append((v1_file, v2_file))
            elif v1_file and not v2_file:
                comparison_pairs.append((v1_file, Path(DEFAULT_FILE)))
            elif not v1_file and v2_file:
                comparison_pairs.append((Path(DEFAULT_FILE), v2_file))

    return comparison_pairs


def run_batch_comparison(comparison_pairs, output_dir=None):
    """
    批量执行比较对的比较任务
    """
    print(f"--- 开始批量比较，共 {len(comparison_pairs)} 个比较对 ---")

    for i, (left_path, right_path) in enumerate(comparison_pairs):
        print(f"\n--- 比较对 {i + 1}/{len(comparison_pairs)} ---")
        print(f"左侧文件: {left_path}")
        print(f"右侧文件: {right_path}")

        if not left_path.exists() and left_path != Path(DEFAULT_FILE):
            print(f"警告: 左侧文件不存在: {left_path}")
            continue
        if not right_path.exists() and right_path != Path(DEFAULT_FILE):
            print(f"警告: 右侧文件不存在: {right_path}")
            continue

        is_left_jar = left_path.name.lower().endswith('.jar') if left_path != Path(DEFAULT_FILE) else False
        is_right_jar = right_path.name.lower().endswith('.jar') if right_path != Path(DEFAULT_FILE) else False

        if is_left_jar and is_right_jar:
            print("检测到JAR文件对，执行比较...")
            html_report_path = run_winmerge_comparison(left_path, right_path, output_dir=output_dir)
            print(f"HTML报告已生成: {html_report_path}")
            continue

        html_report_path = run_winmerge_comparison(left_path, right_path, output_dir=output_dir)
        print(f"HTML报告已生成: {html_report_path}")

    print("\n--- 批量比较完成 ---")
