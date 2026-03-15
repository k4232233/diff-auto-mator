"""
@Author：haoran.xu
"""
import sys
from pathlib import Path

from bs4 import BeautifulSoup

EXTRACTION_REPORT_FILENAME = "extracted_diff_data.txt"
TARGET_DIR = Path("./merge_files")


def generate_extraction_list(report_html_path: Path, output_dir=None) -> Path:
    """
    使用 BeautifulSoup 提取所有数据行 (<tr>)，
    直接提取每个 <td> 单元格的纯文本内容，并格式化为制表符分隔。
    """
    print("\n--- Step 2: 自动解析 HTML 报告并提取差异文件列表 (直接 BS4 提取) ---")

    if not report_html_path.exists():
        print(f"❌ 错误: 找不到 WinMerge HTML 报告文件: {report_html_path}")
        sys.exit(1)

    print(f"🚀 正在解析报告: {report_html_path.name}")

    try:
        with open(report_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"❌ 读取 HTML 报告失败: {e}")
        sys.exit(1)

    soup = BeautifulSoup(html_content, 'html.parser')

    target_table = soup.find('table')

    if not target_table:
        print("❌ 错误: 未在 HTML 中找到预期的 <table> 元素。")
        sys.exit(1)

    extracted_lines = []

    header = "Filename\tFolder\tComparison result"
    extracted_lines.append(header)

    for row in target_table.find_all('tr')[1:]:

        cols = row.find_all('td')

        if len(cols) >= 3:
            filename = cols[0].text.strip()
            folder = cols[1].text.strip()
            comparison_result = cols[2].text.strip()

            line = f"{filename}\t{folder}\t{comparison_result}"
            extracted_lines.append(line)

    if len(extracted_lines) <= 1:
        print("✅ 报告解析完成，但未找到差异文件记录。")
        target_dir = Path(output_dir) if output_dir else TARGET_DIR
        extraction_file = target_dir / EXTRACTION_REPORT_FILENAME
        extraction_file.write_text('', encoding='utf-8')
        return extraction_file

    target_dir = Path(output_dir) if output_dir else TARGET_DIR
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)

    extraction_file = target_dir / f"{report_html_path.stem}_{EXTRACTION_REPORT_FILENAME}"

    try:
        extraction_file.write_text('\n'.join(extracted_lines), encoding='utf-8')
        print(f"✅ 差异文件列表提取成功，已保存到: {extraction_file}")
        return extraction_file
    except Exception as e:
        print(f"❌ 保存提取结果文件失败: {e}")
        sys.exit(1)


# def main():
#     # 示例用法：请将这里的路径替换为您生成的 WinMerge 报告路径
#     report_file_path = TARGET_DIR / "bond-service-api-1.12.6.0.jar_vs_bond-service-api-1.14.4.0.jar_merge_report.html"
#
#     generate_extraction_list(report_file_path)
#
#
# if __name__ == "__main__":
#     main()

