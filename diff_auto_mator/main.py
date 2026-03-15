"""
@Author：haoran.xu
"""
import re
import sys

import os

from pathlib import Path
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from winmerge_to_html import run_winmerge_comparison

from analysis_eport import generate_extraction_list

from relative_path import generate_file_list

from extract_jar_files import extract_jar_diffs

from batch_comparison import generate_comparison_list, run_batch_comparison

from cleanup_files import cleanup_temp_files

from generate_excel import main as generate_excel_report, find_jar_file_paths

from constants import DEFAULT_OUTPUT_DIR, DEFAULT_DECOMPILER_PATH, TARGET_DIR


def run_diff_workflow(left__path: Path, right_path: Path):
    """
    完整的差异分析工作流程：
    1. 用户输入两个JAR文件路径
    2. 使用WinMerge生成HTML差异报告
    3. 解析HTML报告，提取差异文件信息
    4. 生成差异文件的相对路径列表
    5. 根据路径列表提取JAR文件并反编译.class文件
    """
    print("--- 开始执行完整的JAR差异分析工作流程 ---")

    if not left__path.exists():
        print(f"error:找不到左侧JAR文件：{left__path}")
        sys.exit(1)

    if not right_path.exists():
        print(f"error:找不到右侧JAR文件：{right_path}")
        sys.exit(1)

    print(f"左侧JAR: {left__path}")
    print(f"右侧JAR: {right_path}")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    comparison_dir = TARGET_DIR / f"comparison_{timestamp}"
    comparison_dir.mkdir(parents=True, exist_ok=True)
    print(f"创建本次比较的目录: {comparison_dir}")

    print("--- 步骤 2: 使用WinMerge生成HTML差异报告 ---")
    html_report_path = run_winmerge_comparison(left__path, right_path, output_dir=comparison_dir)
    print(f"HTML报告已生成: {html_report_path}")

    print("--- 步骤 3: 解析HTML报告，提取差异文件信息 ---")
    extraction_report_path = generate_extraction_list(html_report_path, output_dir=comparison_dir)
    print(f"差异文件信息已提取: {extraction_report_path}")

    print("--- 步骤 4: 生成差异文件的相对路径 ---")
    try:
        with open(extraction_report_path, 'r', encoding='utf-8') as f:
            input_content = f.read()
        lines = input_content.strip().split('\n')[1:]
        content_without_header = '\n'.join(lines)
    except Exception as e:
        print(f"读取提取报告时发生错误: {e}")
        sys.exit(1)

    result_paths = generate_file_list(content_without_header)

    output_filename = comparison_dir / "file_list_to_extract.txt"
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(result_paths))
        print(f"文件路径列表已生成: {output_filename}")
    except Exception as e:
        print(f"写入文件路径列表时发生错误: {e}")
        sys.exit(1)

    print("--- 步骤 5: 提取JAR文件并反编译.class文件 ---")
    results = extract_jar_diffs(
        left_jar_path=str(left__path),
        right_jar_path=str(right_path),
        file_list_path=str(output_filename),
        target_output_dir=DEFAULT_OUTPUT_DIR,
        decompiler_path=DEFAULT_DECOMPILER_PATH
    )

    if "error" not in results:
        print(f"\n✅ 工作流程完成!")
        print(f"V1输出目录: {results['v1_dir']}")
        print(f"V2输出目录: {results['v2_dir']}")
        if 'summary_file' in results:
            print(f"提取文件路径摘要: {results['summary_file']}")
            return results['summary_file']
    else:
        print(f"\n❌ 工作流程失败: {results['error']}")
        return None


if __name__ == '__main__':
    while True:
        try:
            print("--- 步骤 1: 获取JAR文件路径 ---")

            left_jar_input = input(
                "请输入左侧 (旧) JAR 文件的完整路径 (输入 'exit' 或 'quit' 退出程序): ").strip().strip('"')
            if left_jar_input.lower() in ['exit', 'quit']:
                print("程序退出。")
                break

            left_jar_path = Path(left_jar_input)

            right_jar_input = input("请输入右侧 (新) JAR 文件的完整路径: ").strip().strip('"')
            if right_jar_input.lower() in ['exit', 'quit']:
                print("程序退出。")
                break

            right_jar_path = Path(right_jar_input)

            summary_file_path = run_diff_workflow(left_jar_path, right_jar_path)

            # 获取当前比较的时间戳目录
            comparison_dirs = [d for d in TARGET_DIR.iterdir() if
                               d.is_dir() and d.name.startswith("comparison_")]
            if comparison_dirs:
                current_comparison_dir = max(comparison_dirs, key=os.path.getctime)
            else:
                current_comparison_dir = None

            print("--- 步骤 6: 读取文件列表批量比较 ---")

            # 使用当前比较生成的摘要文件路径
            if summary_file_path:
                latest_extracted_file = Path(summary_file_path)
                if latest_extracted_file.exists():
                    print(f"找到本次比较生成的提取文件路径: {latest_extracted_file}")

                    # 生成比较对
                    comparison_pairs = generate_comparison_list(latest_extracted_file)
                    print(f"生成了 {len(comparison_pairs)} 个比较对")

                    # 执行批量比较，使用当前比较的时间戳目录
                    import os

                    comparison_dirs = [d for d in TARGET_DIR.iterdir() if
                                       d.is_dir() and d.name.startswith("comparison_")]
                    if comparison_dirs:
                        target_comparison_dir = max(comparison_dirs, key=os.path.getctime)
                        run_batch_comparison(comparison_pairs, output_dir=target_comparison_dir)
                    else:
                        # 如果没有找到比较目录，则不指定输出目录，使用默认行为
                        run_batch_comparison(comparison_pairs)
                else:
                    print(f"摘要文件不存在: {latest_extracted_file}")
            else:
                print("当前比较未生成摘要文件，跳过批量比较。")

            print("--- 步骤 7: 生成Excel报告 ---")
            try:
                print("正在生成Excel报告...")
                generate_excel_report()  # 调用Excel生成功能，使用重构后的函数
                print("Excel报告生成完成。")

                # 获取未处理的JAR文件路径
                print("--- 步骤 8: 查找未处理的JAR文件路径 ---")
                jar_file_mapping = find_jar_file_paths()
                if jar_file_mapping:
                    print(f"找到 {len(jar_file_mapping)} 个JAR文件路径映射:")
                    for jar_name, jar_path in jar_file_mapping.items():
                        print(f"  - {jar_name} -> {jar_path}")

                    # TODO: 添加对jar_file_mapping的后续处理逻辑
                    # 检查是否有JAR文件映射用于下一轮比较
                    if jar_file_mapping:
                        print("\n--- 开始下一轮JAR文件比较 ---")
                        # 获取JAR文件路径列表
                        jar_paths = list(jar_file_mapping.values())
                        if len(jar_paths) >= 2:
                            # 按顺序两两分组进行比较
                            for i in range(0, len(jar_paths) - 1, 2):
                                left_jar_path = Path(jar_paths[i])
                                right_jar_path = Path(jar_paths[i + 1])
                                sheet_name = re.sub(r'-\d.*$', '',  Path(left_jar_path).stem)

                                print(f"准备比较: {left_jar_path} 和 {right_jar_path}")

                                # 执行新一轮的比较
                                try:
                                    summary_file_path = run_diff_workflow(left_jar_path, right_jar_path)

                                    print("--- 步骤 6: 读取文件列表批量比较 ---")

                                    # 使用当前比较生成的摘要文件路径
                                    if summary_file_path:
                                        latest_extracted_file = Path(summary_file_path)
                                        if latest_extracted_file.exists():
                                            print(f"找到本次比较生成的提取文件路径: {latest_extracted_file}")

                                            # 生成比较对
                                            comparison_pairs = generate_comparison_list(latest_extracted_file)
                                            print(f"生成了 {len(comparison_pairs)} 个比较对")

                                            # 执行批量比较
                                            comparison_dirs = [d for d in TARGET_DIR.iterdir() if
                                                               d.is_dir() and d.name.startswith("comparison_")]
                                            if comparison_dirs:
                                                target_comparison_dir = max(comparison_dirs, key=os.path.getctime)
                                                run_batch_comparison(comparison_pairs, output_dir=target_comparison_dir)
                                            else:
                                                run_batch_comparison(comparison_pairs)
                                        else:
                                            print(f"摘要文件不存在: {latest_extracted_file}")
                                    else:
                                        print("当前比较未生成摘要文件，跳过批量比较。")

                                    print("--- 步骤 7: 生成Excel报告 (新工作表) ---")
                                    try:
                                        print("正在生成Excel报告到新工作表...")
                                        from generate_excel import add_sheet_to_existing_excel
                                        add_sheet_to_existing_excel(f"pair_{i//2+1}",
                                                                    f"{sheet_name}")  # 调用新工作表生成函数
                                        print("Excel报告生成完成。")
                                    except Exception as e:
                                        print(f"生成Excel报告时发生错误: {e}")

                                except Exception as e:
                                    print(f"处理JAR文件比较时发生错误: {e}")

                                # 如果还有剩余的JAR文件（奇数个的情况），可以考虑如何处理
                                if len(jar_paths) % 2 != 0 and i + 2 == len(jar_paths) - 1:
                                    print(f"剩余一个JAR文件未配对: {jar_paths[-1]}")

                        else:
                            print(f"JAR文件数量不足，无法进行比较 (需要至少2个，当前有{len(jar_paths)}个)。")
                    else:
                        print("没有JAR文件路径用于下一轮比较。")
                else:
                    print("未找到相关的JAR文件路径。")
            except Exception as e:
                print(f"生成Excel报告时发生错误: {e}")

            print("\n" + "=" * 50)
            print("一轮比较完成，可以开始下一轮比较。")
            print("=" * 50 + "\n")
            # # 清理临时文件
            # cleanup_temp_files()

        except KeyboardInterrupt:
            print("\n\n程序被用户中断。")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            continue