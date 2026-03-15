#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DiffAutoMator 标准版本打包脚本
用于创建标准的可执行版本
"""

import os
import sys
import shutil
from pathlib import Path
import subprocess


def create_standard_version():
    print("开始创建DiffAutoMator标准版本...")

    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])

    project_root = Path(__file__).parent
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"

    tools_dir = project_root / "diff_auto_mator" / "tools"
    if not tools_dir.exists():
        tools_dir.mkdir(parents=True, exist_ok=True)
        print(f"创建tools目录: {tools_dir}")

    print("正在打包GUI应用程序...")
    gui_script = project_root / "diff_auto_mator" / "gui_main.py"
    icon_path = tools_dir / "icon.png"

    cmd = [
        "pyinstaller",
        "--name=DiffAutoMator",
        "--onedir",
        "--windowed",
        "--paths", str(project_root / "diff_auto_mator"),
        "--add-data", f"{project_root / 'diff_auto_mator'};diff_auto_mator",
        "--add-data", f"{tools_dir};tools",
        "--collect-all", "PyQt5",
        "--collect-all", "bs4",
        "--collect-all", "lxml",
        "--collect-all", "PIL",
        "--collect-all", "openpyxl",
        "--collect-all", "playwright",
        "--collect-all", "playwright.__pyinstaller",
        "--hidden-import", "winmerge_to_html",
        "--hidden-import", "analysis_eport",
        "--hidden-import", "relative_path",
        "--hidden-import", "extract_jar_files",
        "--hidden-import", "batch_comparison",
        "--hidden-import", "constants",
        "--hidden-import", "extract_shell",
        "--hidden-import", "generate_excel",
    ]

    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])

    cmd.append(str(gui_script))

    try:
        subprocess.run(cmd, check=True)
        print("GUI应用程序打包成功！标准版本位于: dist/DiffAutoMator/")
    except subprocess.CalledProcessError as e:
        print(f"打包过程中出现错误: {e}")
        return False

    print(f"\n标准版本已创建完成: {dist_dir / 'DiffAutoMator'}")
    print("这是一个标准的可执行文件，用户可以自行配置WinMerge路径等依赖项")
    return True


if __name__ == "__main__":
    success = create_standard_version()
    if success:
        print("\n标准版本打包完成！")
    else:
        print("\n打包过程中出现错误，请检查日志。")
