"""
@Author：DiffAutoMator GUI
现代化的JAR文件差异分析工具图形界面
UI Redesign: Natural & Elegant (Refined Layout)
"""

import sys
import os
import io
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar,
                             QFileDialog, QMessageBox, QGroupBox, QTabWidget)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QIcon, QFontDatabase

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from winmerge_to_html import run_winmerge_comparison
from analysis_eport import generate_extraction_list
from relative_path import generate_file_list
from extract_jar_files import extract_jar_diffs
from batch_comparison import generate_comparison_list, run_batch_comparison
from constants import DEFAULT_OUTPUT_DIR, DEFAULT_DECOMPILER_PATH, TARGET_DIR, WINMERGE_PATH, EXCEL_DIR


class EmittingStream(io.IOBase):
    """自定义输出流类"""

    def __init__(self, signal):
        super().__init__()
        self.signal = signal
        self.buffer_content = ""

    def write(self, text):
        self.buffer_content += text
        if '\n' in self.buffer_content:
            lines = self.buffer_content.split('\n')
            self.buffer_content = lines[-1]
            for line in lines[:-1]:
                if line.strip():
                    self.signal.emit(line.strip())
        return len(text)

    def flush(self):
        if self.buffer_content.strip():
            self.signal.emit(self.buffer_content.strip())
            self.buffer_content = ""


class DiffWorker(QThread):
    """
    工作线程，用于在后台执行差异分析任务
    """
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(self, left_path, right_path):
        super().__init__()
        self.left_path = left_path
        self.right_path = right_path

    def run(self):
        try:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            stdout_stream = EmittingStream(self.progress)
            stderr_stream = EmittingStream(self.progress)
            sys.stdout = stdout_stream
            sys.stderr = stderr_stream

            try:
                summary_file_path, comparison_dir = self.run_diff_workflow_with_progress()
                self.finished.emit(
                    str(summary_file_path) if summary_file_path else "", 
                    str(comparison_dir) if comparison_dir else ""
                )
            finally:
                stdout_stream.flush()
                stderr_stream.flush()
                sys.stdout = old_stdout
                sys.stderr = old_stderr
        except Exception as e:
            self.error.emit(str(e))

    def run_diff_workflow_with_progress(self):
        self.progress.emit("--- 开始执行完整的JAR差异分析工作流程 ---")

        if not self.left_path.exists():
            self.progress.emit(f"错误:找不到左侧JAR文件：{self.left_path}")
            return None, None

        if not self.right_path.exists():
            self.progress.emit(f"错误:找不到右侧JAR文件：{self.right_path}")
            return None, None

        self.progress.emit(f"左侧JAR: {self.left_path}")
        self.progress.emit(f"右侧JAR: {self.right_path}")

        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        comparison_dir = TARGET_DIR / f"comparison_{timestamp}"
        comparison_dir.mkdir(parents=True, exist_ok=True)
        self.progress.emit(f"创建本次比较的目录: {comparison_dir}")

        self.progress.emit("--- 步骤 2: 使用WinMerge生成HTML差异报告 ---")
        html_report_path = run_winmerge_comparison(self.left_path, self.right_path, output_dir=comparison_dir)
        self.progress.emit(f"HTML报告已生成: {html_report_path}")

        self.progress.emit("--- 步骤 3: 解析HTML报告，提取差异文件信息 ---")
        extraction_report_path = generate_extraction_list(html_report_path, output_dir=comparison_dir)
        self.progress.emit(f"差异文件信息已提取: {extraction_report_path}")

        self.progress.emit("--- 步骤 4: 生成差异文件的相对路径 ---")
        try:
            with open(extraction_report_path, 'r', encoding='utf-8') as f:
                input_content = f.read()
            lines = input_content.strip().split('\n')[1:]
            content_without_header = '\n'.join(lines)
        except Exception as e:
            self.progress.emit(f"读取提取报告时发生错误: {e}")
            return None, None

        result_paths = generate_file_list(content_without_header)

        output_filename = comparison_dir / "file_list_to_extract.txt"
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(result_paths))
            self.progress.emit(f"文件路径列表已生成: {output_filename}")
        except Exception as e:
            self.progress.emit(f"写入文件路径列表时发生错误: {e}")
            return None, None

        self.progress.emit("--- 步骤 5: 提取JAR文件并反编译.class文件 ---")
        results = extract_jar_diffs(
            left_jar_path=str(self.left_path),
            right_jar_path=str(self.right_path),
            file_list_path=str(output_filename),
            target_output_dir=DEFAULT_OUTPUT_DIR,
            decompiler_path=DEFAULT_DECOMPILER_PATH
        )

        if "error" not in results:
            self.progress.emit(f"\n✅ 前5步工作流程完成!")
            self.progress.emit(f"V1输出目录: {results['v1_dir']}")
            self.progress.emit(f"V2输出目录: {results['v2_dir']}")
            if 'summary_file' in results:
                self.progress.emit(f"提取文件路径摘要: {results['summary_file']}")

                self.progress.emit("--- 步骤 6: 读取文件列表批量比较 ---")

                summary_file_path = results['summary_file']
                latest_extracted_file = Path(summary_file_path)

                if latest_extracted_file.exists():
                    self.progress.emit(f"找到本次比较生成的提取文件路径: {latest_extracted_file}")

                    comparison_pairs = generate_comparison_list(latest_extracted_file)
                    self.progress.emit(f"生成了 {len(comparison_pairs)} 个比较对")

                    import os

                    comparison_dirs = [d for d in TARGET_DIR.iterdir() if
                                       d.is_dir() and d.name.startswith("comparison_")]
                    if comparison_dirs:
                        target_comparison_dir = max(comparison_dirs, key=os.path.getctime)
                        run_batch_comparison(comparison_pairs, output_dir=target_comparison_dir)
                        self.progress.emit(f"批量比较完成，输出到目录: {target_comparison_dir}")
                    else:
                        run_batch_comparison(comparison_pairs)
                        self.progress.emit("批量比较完成")
                else:
                    self.progress.emit(f"摘要文件不存在: {latest_extracted_file}")
                self.progress.emit("--- 步骤 7: 生成Excel报告 ---")
                try:
                    self.progress.emit("正在生成Excel报告...")
                    from generate_excel import main as generate_excel_report
                    generate_excel_report()
                    self.progress.emit("Excel报告生成完成。")

                    self.progress.emit("--- 步骤 8: 查找未处理的JAR文件路径 ---")
                    from generate_excel import find_jar_file_paths
                    jar_file_mapping = find_jar_file_paths()
                    if jar_file_mapping:
                        self.progress.emit(f"找到 {len(jar_file_mapping)} 个JAR文件路径映射:")
                        for jar_name, jar_path in jar_file_mapping.items():
                            self.progress.emit(f"  - {jar_name} -> {jar_path}")

                        if jar_file_mapping:
                            self.progress.emit("\n--- 开始下一轮JAR文件比较 ---")
                            import re
                            jar_paths = list(jar_file_mapping.values())
                            if len(jar_paths) >= 2:
                                for i in range(0, len(jar_paths) - 1, 2):
                                    left_jar_path = Path(jar_paths[i])
                                    right_jar_path = Path(jar_paths[i + 1])
                                    sheet_name = re.sub(r'-\d.*$', '', Path(left_jar_path).stem)

                                    self.progress.emit(f"准备比较: {left_jar_path} 和 {right_jar_path}")

                                    from datetime import datetime
                                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                    comparison_dir_new = TARGET_DIR / f"comparison_{timestamp}"
                                    comparison_dir_new.mkdir(parents=True, exist_ok=True)
                                    self.progress.emit(f"创建本次比较的目录: {comparison_dir_new}")

                                    self.progress.emit("--- 步骤 2: 使用WinMerge生成HTML差异报告 ---")
                                    html_report_path = run_winmerge_comparison(left_jar_path, right_jar_path,
                                                                               output_dir=comparison_dir_new)
                                    self.progress.emit(f"HTML报告已生成: {html_report_path}")

                                    self.progress.emit("--- 步骤 3: 解析HTML报告，提取差异文件信息 ---")
                                    extraction_report_path = generate_extraction_list(html_report_path,
                                                                                      output_dir=comparison_dir_new)
                                    self.progress.emit(f"差异文件信息已提取: {extraction_report_path}")

                                    self.progress.emit("--- 步骤 4: 生成差异文件的相对路径 ---")
                                    try:
                                        with open(extraction_report_path, 'r', encoding='utf-8') as f:
                                            input_content = f.read()
                                        lines = input_content.strip().split('\n')[1:]
                                        content_without_header = '\n'.join(lines)
                                    except Exception as e:
                                        self.progress.emit(f"读取提取报告时发生错误: {e}")
                                        continue

                                    result_paths = generate_file_list(content_without_header)

                                    output_filename = comparison_dir_new / "file_list_to_extract.txt"
                                    try:
                                        with open(output_filename, 'w', encoding='utf-8') as f:
                                            f.write('\n'.join(result_paths))
                                        self.progress.emit(f"文件路径列表已生成: {output_filename}")
                                    except Exception as e:
                                        self.progress.emit(f"写入文件路径列表时发生错误: {e}")
                                        continue

                                    self.progress.emit("--- 步骤 5: 提取JAR文件并反编译.class文件 ---")
                                    results = extract_jar_diffs(
                                        left_jar_path=str(left_jar_path),
                                        right_jar_path=str(right_jar_path),
                                        file_list_path=str(output_filename),
                                        target_output_dir=DEFAULT_OUTPUT_DIR,
                                        decompiler_path=DEFAULT_DECOMPILER_PATH
                                    )

                                    if "error" not in results:
                                        self.progress.emit(f"\n✅ 下一轮工作流程完成!")
                                        self.progress.emit(f"V1输出目录: {results['v1_dir']}")
                                        self.progress.emit(f"V2输出目录: {results['v2_dir']}")

                                        if 'summary_file' in results:
                                            self.progress.emit("--- 步骤 6: 读取文件列表批量比较 ---")

                                            latest_extracted_file = Path(results['summary_file'])

                                            if latest_extracted_file.exists():
                                                self.progress.emit(
                                                    f"找到本次比较生成的提取文件路径: {latest_extracted_file}")

                                                comparison_pairs = generate_comparison_list(latest_extracted_file)
                                                self.progress.emit(f"生成了 {len(comparison_pairs)} 个比较对")

                                                comparison_dirs = [d for d in TARGET_DIR.iterdir() if
                                                                   d.is_dir() and d.name.startswith("comparison_")]
                                                if comparison_dirs:
                                                    target_comparison_dir = max(comparison_dirs, key=os.path.getctime)
                                                    run_batch_comparison(comparison_pairs,
                                                                         output_dir=target_comparison_dir)
                                                    self.progress.emit(
                                                        f"批量比较完成，输出到目录: {target_comparison_dir}")
                                                else:
                                                    run_batch_comparison(comparison_pairs)
                                                    self.progress.emit("批量比较完成")
                                            else:
                                                self.progress.emit(f"摘要文件不存在: {latest_extracted_file}")

                                        self.progress.emit("--- 步骤 7: 生成Excel报告 (新工作表) ---")
                                        try:
                                            self.progress.emit("正在生成Excel报告到新工作表...")
                                            from generate_excel import add_sheet_to_existing_excel
                                            add_sheet_to_existing_excel(f"pair_{i // 2 + 1}",
                                                                        f"{sheet_name}")
                                            self.progress.emit("Excel新工作表生成完成。")
                                        except Exception as e:
                                            self.progress.emit(f"生成Excel新工作表时发生错误: {e}")

                                    else:
                                        self.progress.emit(f"\n❌ 下一轮工作流程失败: {results['error']}")

                                    if len(jar_paths) % 2 != 0 and i + 2 == len(jar_paths) - 1:
                                        self.progress.emit(f"剩余一个JAR文件未配对: {jar_paths[-1]}")

                            else:
                                self.progress.emit(
                                    f"JAR文件数量不足，无法进行比较 (需要至少2个，当前有{len(jar_paths)}个)。")
                        else:
                            self.progress.emit("没有JAR文件路径用于下一轮比较。")
                    else:
                        self.progress.emit("未找到相关的JAR文件路径。")
                except Exception as e:
                    self.progress.emit(f"生成Excel报告时发生错误: {e}")

                self.progress.emit(f"\n✅ 完整的工作流程完成!")
                return results['summary_file'], comparison_dir
            else:
                self.progress.emit(f"\n⚠️  工作流程部分完成（缺少摘要文件）")
                return None, comparison_dir
        else:
            self.progress.emit(f"\n❌ 工作流程失败: {results['error']}")
            return None, comparison_dir


class ModernGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DiffAutoMator")
        self.resize(1024, 800)  # 稍微加宽，适应现代屏幕

        # 加载并使用其他字体
        font_path = Path(__file__).parent / "tools" / "diy_font.ttf"
        if font_path.exists():
            # 从文件加载字体
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            if font_id != -1:
                font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                font = QFont(font_family, 10)
            else:
                # 如果字体加载失败，回退到系统默认字体
                font = QFont("Microsoft YaHei UI", 10)
        else:
            # 如果字体文件不存在，使用系统默认字体
            font = QFont("Microsoft YaHei UI", 10)
        font.setStyleStrategy(QFont.PreferAntialias)
        QApplication.setFont(font)

        self.setup_styles()
        self.init_ui()

    def setup_styles(self):
        """
        样式表优化重点：
        1. 增加 Padding (内边距) 让界面有呼吸感
        2. 弱化边框颜色，使用阴影代替硬边框
        3. 调整 Tab 样式，防止文字截断
        """
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F8F9FA; /* 极淡的灰白背景，比纯白护眼 */
            }
            QWidget {
                color: #333333;
                outline: none;
            }

            /* --- Tab 标签页优化 --- */
            QTabWidget::pane {
                border: none;
                background: transparent;
                margin-top: 15px; /* Tab内容与标签栏的间距 */
            }
            QTabWidget::tab-bar {
                alignment: left; /* 左对齐更符合阅读习惯 */
                left: 15px;
            }
            QTabBar::tab {
                background: transparent;
                color: #666666;
                padding: 10px 16px; /* 舒适的点击区域 */
                font-weight: 480;
                font-size: 13px;
                border-bottom: 3px solid transparent;
                margin-right: 5px;
            }
            QTabBar::tab:hover {
                color: #2563EB;
                background-color: rgba(37, 99, 235, 0.05);
                border-radius: 4px 4px 0 0;
            }
            QTabBar::tab:selected {
                color: #2563EB;
                border-bottom: 3px solid #2563EB; /* 仅底部有线条，简洁 */
            }

            /* --- 卡片容器 (GroupBox) --- */
            QGroupBox {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB; /* 极淡的边框 */
                border-radius: 10px;
                margin-top: 10px; /* 给标题留位置 */
                padding: 20px; /* 内部大留白 */
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 15px;
                color: #111827; /* 深黑色标题 */
                font-weight: bold;
                font-size: 14px;
            }

            /* --- 输入框 --- */
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                background-color: #FFFFFF;
                font-size: 13px;
                min-height: 20px; /* 保证高度舒适 */
                color: #374151;
            }
            QLineEdit:hover {
                border-color: #9CA3AF;
            }
            QLineEdit:focus {
                border: 1px solid #2563EB;
                background-color: #FFFFFF;
            }
            QLineEdit:disabled {
                background-color: #F3F4F6;
                color: #9CA3AF;
            }

            /* --- 按钮体系 --- */
            QPushButton {
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
                padding: 8px 16px;
            }

            /* 浏览按钮：幽灵风格 (Outline) */
            QPushButton#browseButton {
                background-color: #FFFFFF;
                color: #4B5563;
                border: 1px solid #D1D5DB;
            }
            QPushButton#browseButton:hover {
                background-color: #F9FAFB;
                border-color: #6B7280;
                color: #111827;
            }
            QPushButton#browseButton:pressed {
                background-color: #F3F4F6;
            }

            /* 主按钮：蓝色实心 */
            QPushButton#startButton {
                background-color: #2563EB;
                color: white;
                border: none;
                font-size: 14px;
                padding: 10px 24px;
            }
            QPushButton#startButton:hover {
                background-color: #1D4ED8;
                margin-top: -1px; /* 悬浮微动效 */
            }
            QPushButton#startButton:pressed {
                background-color: #1E40AF;
                margin-top: 1px;
            }
            QPushButton#startButton:disabled {
                background-color: #93C5FD;
                color: #EFF6FF;
            }

            /* 停止按钮：红色实心 */
            QPushButton#stopButton {
                background-color: #EF4444;
                color: white;
                border: none;
                font-size: 14px;
                padding: 10px 24px;
            }
            QPushButton#stopButton:hover {
                background-color: #DC2626;
            }

            /* 重置按钮：纯文字 */
            QPushButton#resetButton {
                background-color: transparent;
                color: #6B7280;
                border: none;
            }
            QPushButton#resetButton:hover {
                color: #374151;
                background-color: #F3F4F6;
            }

            /* --- 日志区域 --- */
            QTextEdit {
                background-color: #1E1E1E; /* 纯黑背景对比度太高，用深灰 */
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 8px;
                font-family: 'Consolas', 'JetBrains Mono', 'Monaco', monospace;
                font-size: 12px;
                padding: 12px;
                line-height: 1.5; /* 增加行距 */
            }

            /* --- 状态栏 --- */
            QStatusBar {
                background: #FFFFFF;
                color: #6B7280;
                border-top: 1px solid #E5E7EB;
                min-height: 28px;
            }
        """)

    def init_ui(self):
        # 菜单栏设置
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar { background-color: #FFFFFF; border-bottom: 1px solid #F3F4F6; padding: 4px; }
            QMenuBar::item { spacing: 10px; padding: 6px 12px; color: #4B5563; border-radius: 4px; }
            QMenuBar::item:selected { background-color: #F3F4F6; color: #111827; }
        """)

        file_menu = menubar.addMenu('文件')
        file_menu.addAction('打开旧版本JAR', self.browse_left_jar)
        file_menu.addSeparator()
        file_menu.addAction('退出', self.close)

        tools_menu = menubar.addMenu('工具')
        tools_menu.addAction('偏好设置', lambda: self.centralWidget().findChild(QTabWidget).setCurrentIndex(1))

        help_menu = menubar.addMenu('帮助')
        help_menu.addAction('关于', self.show_about)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        # 增加外边距，让整个界面不贴边
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # 顶部：Logo 与 标题
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 10)

        # 使用文字排版代替复杂图标
        title_box = QVBoxLayout()
        title_main = QLabel("DiffAutoMator")
        title_main.setStyleSheet("font-size: 26px; font-weight: 800; color: #111827; letter-spacing: 0.5px;")
        title_sub = QLabel("JAR 文件差异分析工具")
        title_sub.setStyleSheet("font-size: 13px; color: #6B7280; margin-top: 4px;")
        title_box.addWidget(title_main)
        title_box.addWidget(title_sub)

        header_layout.addLayout(title_box)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # 标签页容器
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # 初始化页面
        tab_widget.addTab(self.create_main_tab(), "任务配置")
        tab_widget.addTab(self.create_settings_tab(), "系统设置")
        tab_widget.addTab(self.create_log_tab(), "运行日志")

        # 状态栏
        self.statusBar().showMessage("准备就绪")

    def create_input_block(self, title, line_edit, browse_callback, placeholder=""):
        """
        辅助函数：创建垂直堆叠的输入块 (Label在上, Input+Button在下)
        这种布局比 FormLayout 更适应长路径显示
        """
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)  # Label和Input之间的距离

        # 标题 Label
        lbl = QLabel(title)
        lbl.setStyleSheet("font-weight: 600; color: #374151; font-size: 13px;")
        layout.addWidget(lbl)

        # Input + Button 行
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)  # Input和Button之间的距离

        line_edit.setPlaceholderText(placeholder)
        row_layout.addWidget(line_edit)

        btn = QPushButton("浏览")
        btn.setObjectName("browseButton")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(browse_callback)
        btn.setFixedWidth(80)  # 固定宽度
        row_layout.addWidget(btn)

        layout.addWidget(row_widget)
        return container

    def create_main_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(25)  # 组与组之间的间距
        layout.setContentsMargins(5, 5, 5, 5)  # 稍微留一点边

        # --- 卡片1: 源文件选择 ---
        file_group = QGroupBox("比较源 (Source)")
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(20)  # 两个输入框之间的距离

        self.left_jar_input = QLineEdit()
        file_layout.addWidget(self.create_input_block(
            "旧版本 JAR (Base Version)",
            self.left_jar_input,
            self.browse_left_jar,
            "例如: app-v1.0.jar"
        ))

        self.right_jar_input = QLineEdit()
        file_layout.addWidget(self.create_input_block(
            "新版本 JAR (Target Version)",
            self.right_jar_input,
            self.browse_right_jar,
            "例如: app-v2.0.jar"
        ))

        layout.addWidget(file_group)

        # --- 卡片2: 输出设置 ---
        output_group = QGroupBox("输出 (Output)")
        output_layout = QVBoxLayout(output_group)

        self.output_dir_input = QLineEdit(EXCEL_DIR)
        output_layout.addWidget(self.create_input_block(
            "结果保存目录",
            self.output_dir_input,
            self.browse_output_dir
        ))

        layout.addWidget(output_group)

        # 进度条 (放在操作栏上方，视觉分离)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(4)  # 极简线条风格
        self.progress_bar.setStyleSheet("""
            QProgressBar { background: #E5E7EB; border: none; border-radius: 2px; }
            QProgressBar::chunk { background: #2563EB; border-radius: 2px; }
        """)
        layout.addWidget(self.progress_bar)

        layout.addStretch()  # 挤压底部

        # --- 底部操作栏 ---
        action_bar = QHBoxLayout()
        action_bar.setContentsMargins(0, 10, 0, 0)

        self.reset_button = QPushButton("重置所有")
        self.reset_button.setObjectName("resetButton")
        self.reset_button.setCursor(Qt.PointingHandCursor)
        self.reset_button.clicked.connect(self.reset_fields)
        self.reset_button.setFixedWidth(100)

        self.stop_button = QPushButton("停止任务")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setCursor(Qt.PointingHandCursor)
        self.stop_button.clicked.connect(self.stop_comparison)
        self.stop_button.setEnabled(False)
        self.stop_button.setVisible(False)  # 默认隐藏，开始后显示

        self.start_button = QPushButton("开始分析")
        self.start_button.setObjectName("startButton")
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.clicked.connect(self.start_comparison)
        self.start_button.setMinimumWidth(140)  # 主按钮宽一点

        action_bar.addWidget(self.reset_button)
        action_bar.addStretch()
        action_bar.addWidget(self.stop_button)
        action_bar.addWidget(self.start_button)

        layout.addLayout(action_bar)

        return tab

    def create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(25)
        layout.setContentsMargins(5, 5, 5, 5)

        # 工具配置
        tool_group = QGroupBox("外部工具路径")
        tool_layout = QVBoxLayout(tool_group)
        tool_layout.setSpacing(20)

        self.decompiler_path_input = QLineEdit(DEFAULT_DECOMPILER_PATH)
        tool_layout.addWidget(self.create_input_block(
            "Java 反编译器 (Decompiler Jar)",
            self.decompiler_path_input,
            self.browse_decompiler
        ))

        self.winmerge_path_input = QLineEdit(str(WINMERGE_PATH))
        tool_layout.addWidget(self.create_input_block(
            "WinMerge 可执行文件 (Diff Tool)",
            self.winmerge_path_input,
            self.browse_winmerge
        ))

        layout.addWidget(tool_group)

        # 中间产物
        adv_group = QGroupBox("高级配置")
        adv_layout = QVBoxLayout(adv_group)

        self.target_dir_input = QLineEdit(str(TARGET_DIR))
        adv_layout.addWidget(self.create_input_block(
            "临时文件存储目录",
            self.target_dir_input,
            self.browse_target_dir
        ))

        layout.addWidget(adv_group)
        layout.addStretch()

        return tab

    def create_log_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        # 🐛 修复：增加边距，防止顶部标签文字被裁切
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 日志顶部工具栏
        toolbar = QHBoxLayout()
        lbl = QLabel("任务执行日志")
        lbl.setStyleSheet("font-weight: bold; color: #4B5563; font-size: 14px;")

        clear_btn = QPushButton("清空")
        # 🐛 修复：增加按钮高度，确保文字完整显示
        clear_btn.setFixedSize(60, 30)
        clear_btn.setStyleSheet("""
            /* 🐛 修复：为清空按钮增加内部垂直 padding，确保文字居中且不被裁切 */
            QPushButton { background: white; border: 1px solid #D1D5DB; border-radius: 4px; font-size: 12px; color: #6B7280; padding: 3px 6px; } 
            QPushButton:hover { background: #F3F4F6; color: #374151; }
        """)
        clear_btn.clicked.connect(self.clear_log)

        toolbar.addWidget(lbl)
        toolbar.addStretch()
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText(">> 等待任务启动...\n>> 详细的处理日志将实时显示在这里。")
        layout.addWidget(self.log_text)

        return tab

    # --- 逻辑控制函数 ---

    def show_about(self):
        QMessageBox.about(self, "关于 DiffAutoMator",
                          "<h3>DiffAutoMator</h3>"
                          "<p style='color:#666'>版本: 1.0.0</p>"
                          "<p>专为开发者设计的 JAR 差异分析工具。</p>"
                          "<p>By 绘衣</p>")

    def browse_left_jar(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择旧版本 JAR", "", "JAR Files (*.jar);;All Files (*)")
        if file_path: self.left_jar_input.setText(file_path)

    def browse_right_jar(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择新版本 JAR", "", "JAR Files (*.jar);;All Files (*)")
        if file_path: self.right_jar_input.setText(file_path)

    def browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path: self.output_dir_input.setText(dir_path)

    def browse_decompiler(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择反编译器 JAR", "", "JAR Files (*.jar);;All Files (*)")
        if file_path: self.decompiler_path_input.setText(file_path)

    def browse_winmerge(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择 WinMerge.exe", "",
                                                   "Executable Files (*.exe);;All Files (*)")
        if file_path: self.winmerge_path_input.setText(file_path)

    def browse_target_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择目标目录")
        if dir_path: self.target_dir_input.setText(dir_path)

    def start_comparison(self):
        left_path = self.left_jar_input.text().strip()
        right_path = self.right_jar_input.text().strip()

        if not left_path or not right_path:
            QMessageBox.warning(self, "参数缺失", "请确保已选择两个 JAR 文件。")
            return

        if not Path(left_path).exists():
            QMessageBox.critical(self, "文件错误", f"文件不存在:\n{left_path}")
            return
        if not Path(right_path).exists():
            QMessageBox.critical(self, "文件错误", f"文件不存在:\n{right_path}")
            return

        # UI 状态更新
        self.start_button.setEnabled(False)
        self.start_button.setText("分析运行中...")
        self.stop_button.setVisible(True)
        self.stop_button.setEnabled(True)
        self.reset_button.setEnabled(False)
        self.progress_bar.setVisible(True)

        # 自动切到日志页
        self.centralWidget().findChild(QTabWidget).setCurrentIndex(2)
        self.log_text.clear()
        self.statusBar().showMessage("正在运行差异分析...")

        self.worker = DiffWorker(Path(left_path), Path(right_path))
        self.worker.progress.connect(self.update_log)
        self.worker.finished.connect(self.comparison_finished)
        # self.worker.error.connect(self.comparison_error)
        self.worker.start()

    def stop_comparison(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self.update_log("\n[!!!] 用户强制终止了任务。")
        self.reset_ui_state()
        self.statusBar().showMessage("任务已终止")

    def comparison_finished(self, summary_file_path, comparison_dir):
        self.reset_ui_state()
        if summary_file_path and summary_file_path != "None":
            self.statusBar().showMessage("分析成功")
            self.update_log(f"\n[完成] 摘要文件生成于: {summary_file_path}")

            # 询问用户是否打开Excel输出目录
            reply = QMessageBox.question(self, "Complete",
                                         "Analysis completed! Open Excel output directory?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                import os
                from pathlib import Path
                # 打开Excel输出目录
                excel_dir = Path("excel_files")
                if excel_dir.exists():
                    os.startfile(str(excel_dir)) if os.name == 'nt' else None
                else:
                    # 如果excel_files目录不存在，创建并打开
                    excel_dir.mkdir(parents=True, exist_ok=True)
                    os.startfile(str(excel_dir)) if os.name == 'nt' else None
        else:
            self.statusBar().showMessage("Analysis ended (no results)")
            QMessageBox.information(self, "Info", "Analysis process ended without generating summary file.")

    def comparison_error(self, error_msg):
        self.reset_ui_state()
        self.statusBar().showMessage("发生错误")
        self.update_log(f"\n[错误] {error_msg}")
        QMessageBox.critical(self, "异常", f"运行中发生错误:\n{error_msg}")

    def reset_ui_state(self):
        self.start_button.setEnabled(True)
        self.start_button.setText("开始分析")
        self.stop_button.setVisible(False)
        self.reset_button.setEnabled(True)
        self.progress_bar.setVisible(False)

    def update_log(self, message):
        self.log_text.append(message)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def reset_fields(self):
        self.left_jar_input.clear()
        self.right_jar_input.clear()
        self.output_dir_input.setText(DEFAULT_OUTPUT_DIR)
        self.log_text.clear()
        self.statusBar().showMessage("已重置")

    def clear_log(self):
        self.log_text.clear()


def main():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setApplicationName("DiffAutoMator")
    
    # 设置应用程序图标
    icon_path = Path(__file__).parent / "tools" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = ModernGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()