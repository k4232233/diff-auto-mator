# DiffAutoMator

<div align="center">

  <img src="https://img.20011031.xyz/DiffAutoMator2.png" alt="DiffAutoMator Logo" width="120" style="margin-bottom: 16px;"/>

  <p>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.8%2B-blue" alt="Python 3.8+" /></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License" /></a>
    <a href="https://winmerge.org/"><img src="https://img.shields.io/badge/dependency-WinMerge-orange" alt="WinMerge" /></a>
  </p>

  <p><strong>JAR 文件差异分析自动化工具</strong></p>

  <p>一个功能全面的 JAR 文件差异分析自动化工具，通过 WinMerge 比较两个 JAR 文件，解析差异报告，提取差异文件，反编译 .class 文件为可读的源代码，并生成批量比较任务和 Excel 报告，形成完整的 JAR 文件差异分析工作流程。</p>

<table style="width: 100%; table-layout: fixed;">
  <tr>
    <td align="center"><img src="https://img.20011031.xyz/2026-03-24%20144327.png" width="100%"></td>
    <td align="center"><img src="https://img.20011031.xyz/2026-03-24%20153951.png" width="100%"></td>
    <td align="center"><img src="https://img.20011031.xyz/2026-03-24%20154153.png" width="100%"></td>
  </tr>
</table>

</div>

## 🚀 Quickstart
1. 在发布地址下载并解压打包好的免安装压缩包
2. 双击 `.exe` 文件

## :deciduous_tree: 执行文件目录

此目录结构是通过 PyInstaller 打包工具生成的单目录可执行程序，包含了运行 DiffAutoMator 所需的所有依赖文件和库。用户只需运行 `DiffAutoMator.exe` 即可启动应用程序，无需安装 Python 或其他依赖项。

```
DiffAutoMator/
├── _internal             	        # 内部库文件
├── excel_files/                    # excle输出文件
├── ExtractedDiffs/                 # 提取的Jar文件
├── merge_files/                    # 比较文件
├── png_cache/                      # 截图缓存文件
└── DiffAutoMator.exe             	# 主程序可执行文件
```

##  :star: 功能特性

- **WinMerge 对比**: 使用 WinMerge 生成两个 JAR 文件的 HTML 差异报告
- **HTML 报告解析**: 解析 HTML 报告，提取差异文件信息
- **路径生成**: 从解析结果中生成差异文件的相对路径列表
- **JAR 文件提取**: 根据路径列表从两个 JAR 文件中提取指定文件
- **反编译**: 将 `.class` 文件反编译为 Java 源代码
- **批量比较**: 生成并执行批量文件比较任务
- **Excel 报告生成**: 生成包含差异截图的 Excel 报告
- **自动化处理**: 自动检测并处理相关 JAR 文件的比较
- **现代化 GUI**: 提供现代化的图形用户界面操作方式
- **多轮比较**: 支持在一次运行中完成多轮 JAR 文件比较
- **新工作表功能**: 可在现有 Excel 报告中添加新的比较工作表
- **便携版本构建**: 提供打包脚本创建可执行版本
- **智能截图处理**: 使用 Playwright 进行智能截图，优化图片并去除白边
- **清理**: 可选择清理临时文件

## 📋 依赖项

- Python 3.7+
- WinMerge (用于文件比较) - [下载地址](https://winmerge.org/)
- CFR (用于反编译)
- PyQt5 (用于图形界面)
- BeautifulSoup4 (用于 HTML 解析)
- Pillow (用于图像处理)
- OpenPyXL (用于 Excel 生成)
- Playwright (用于截图)
- PyInstaller (用于打包可执行文件)

## 🛠️ 开发者

### 环境准备

1. 确保已安装 Python 3.14+
2. 安装 WinMerge 并将其路径设置在 `constants.py` 中
3. 确保系统中已安装 Java 环境

### 依赖安装

```bash
pip install PyQt5 beautifulsoup4 pillow openpyxl playwright PyInstaller
```

### Playwright 设置

```bash
playwright install chromium
```

## 🚀 使用方式

### 命令行方式

1. 运行主程序：
   ```bash
   python diff_auto_mator/main.py
   ```

2. 按提示输入两个 JAR 文件的路径（左侧为旧版本，右侧为新版本）

3. 系统将自动执行完整的差异分析工作流程，包括后续相关 JAR 文件的自动检测和比较

### 图形界面方式（推荐）

1. 运行 GUI 程序：
   ```bash
   python diff_auto_mator/gui_main.py
   ```

2. 在图形化界面中选择JAR文件并执行比较

3. 使用标签界面进行系统设置和查看运行日志

## 🏗️ 项目架构

```
diff_auto_mator/
├── main.py                 # 主工作流程
├── gui_main.py             # 现代化图形界面
├── constants.py            # 常量定义
├── winmerge_to_html.py     # WinMerge 对比
├── analysis_eport.py       # HTML 报告解析
├── relative_path.py        # 路径生成
├── extract_jar_files.py    # JAR 提取和反编译
├── batch_comparison.py     # 批量比较
├── generate_excel.py       # Excel报告生成
├── cleanup_files.py        # 文件清理
├── build_portable.py       # 打包可执行版本
├── extract_shell.py        # PowerShell脚本集成（备用）
├── ExtractedDiffs/         # 提取的 JAR 文件输出目录
├── excel_files/            # Excel 报告输出目录
├── merge_files/            # 比较报告输出目录
├── png_cache/              # PNG 缓存目录
├── test_demo/              # 测试演示文件
├── tools/                  # 工具目录（包含 CFR 反编译器等）
│   ├── cfr-0.152.jar       # Java反编译器
│   ├── diy_font.ttf        # 自定义字体文件
│   ├── icon.png            # 应用程序图标
│   ├── favicon.ico         # 网站图标
│   ├── ExtractJarFiles_final.ps1  # PowerShell脚本
│   ├── chromium-1200/      # Chromium浏览器
│   ├── chromium_headless_shell-1200/  # Chromium无头浏览器
│   ├── ffmpeg-1011/        # FFmpeg工具
│   └── winldd-1007/        # Windows依赖检查工具
└── build/                  # 构建输出目录
```

## ⚙️ 配置

### 常量配置

`constants.py` 文件中的主要配置项：

- `DEFAULT_OUTPUT_DIR`: 默认输出目录 `./ExtractedDiffs`
- `DEFAULT_DECOMPILER_PATH`: 默认反编译器路径 `./tools/cfr-0.152.jar`
- `WINMERGE_PATH`: WinMerge 可执行文件路径
- `TARGET_DIR`: 目标目录 `./merge_files`
- `EXCEL_DIR`: Excel 输出目录 `./excel_files`
- `PNG_CACHE_DIR`: PNG 缓存目录 `./png_cache`
- `GLOBAL_FONT`: Excel报告使用的全局字体
- `MAX_HEIGHT_LIMIT`: Excel图片高度限制（25000px）

### 工作流程

1. 用户输入两个 JAR 文件路径
2. 使用 WinMerge 生成 HTML 差异报告
3. 解析 HTML 报告，提取差异文件信息
4. 生成差异文件的相对路径列表
5. 根据路径列表提取 JAR 文件并反编译 `.class` 文件
6. 读取文件列表执行批量比较
7. 生成 Excel 报告和截图
8. （可选）清理临时文件
9. 自动检测相关 JAR 文件并进行后续比较
10. 在现有Excel报告中添加新的工作表

## 🔧 构建可执行文件

```bash
python build_portable.py
```
