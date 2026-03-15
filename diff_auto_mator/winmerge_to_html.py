"""
@Author：haoran.xu
"""
import subprocess
import sys
from pathlib import Path

from constants import WINMERGE_PATH, TARGET_DIR, HTML_REPORT_FILENAME


def run_winmerge_comparison(left_path: Path, right_path: Path, output_dir=None) -> Path:
    """
    执行 WinMerge 对比，生成 HTML 报告。
    """
    print("\n--- Step 1: 运行 WinMerge 对比并生成报告 ---")

    if not WINMERGE_PATH.exists():
        print(f"❌ 错误: 找不到 WinMerge 可执行文件: {WINMERGE_PATH}")
        sys.exit(1)

    target_dir = Path(output_dir) if output_dir else TARGET_DIR
    
    if not target_dir.exists():
        print(f"创建目标报告目录: {target_dir}")
        target_dir.mkdir(parents=True, exist_ok=True)

    if left_path.name == 'Untitled':
        report_file = target_dir / f"{right_path.name}_{HTML_REPORT_FILENAME}"
    elif right_path.name == 'Untitled':
        report_file = target_dir / f"{left_path.name}_{HTML_REPORT_FILENAME}"
    elif right_path.name == left_path.name:
        report_file = target_dir / f"{left_path.name}_{HTML_REPORT_FILENAME}"
    else:
        report_file = target_dir / f"{left_path.name}_vs_{right_path.name}_{HTML_REPORT_FILENAME}"
    
    print(f"🚀 正在启动 WinMerge (左: {left_path.name}, 右: {right_path.name})...")
    print(f"   报告将输出到: {report_file}")

    command = [
        str(WINMERGE_PATH),
        str(left_path),
        str(right_path),
        "/cfg", "Settings/DiffContextV2=10",
        "/cfg", "ReportFiles/ReportType=2",
        "/noninteractive",
        "/minimize",
        "/or", str(report_file)
    ]

    try:
        subprocess.run(command, check=True, creationflags=subprocess.CREATE_NO_WINDOW)

        if report_file.exists():
            print("✅ WinMerge 报告生成成功。")
            return report_file
        else:
            print("❌ WinMerge 报告文件未找到，请检查 WinMerge 路径或权限。")
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"❌ 运行 WinMerge 失败，返回错误代码: {e.returncode}")
        sys.exit(1)
