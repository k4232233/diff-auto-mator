"""
@Author：haoran.xu
"""
from pathlib import Path

FILE_LIST_TO_EXTRACT = r"./file_list_to_extract.txt"
def extract_base_name(jar_name):
    # 分离文件名和扩展名

    name_part = jar_name[:-4]  # 去掉 .jar 扩展名

    # 按 '-' 分割

    parts = name_part.split('-')

    # 从后往前判断，连续的部分如果看起来像版本号就跳过

    # 版本号通常是数字和点的组合，如 '1', '14', '1.12', '1.12.6.0' 等

    i = len(parts) - 1

    while i >= 0:

        part = parts[i]

        # 检查是否是版本号：包含数字，且可能包含点号

        if any(c.isdigit() for c in part) and all(c.isdigit() or c == '.' for c in part):

            # 继续向前检查

            i -= 1

        else:

            # 找到了非版本部分，停止

            break

    # 非版本部分的索引范围是 0 到 i（包含i）

    if i >= 0:
        non_version_parts = parts[:i + 1]

        base_name = '-'.join(non_version_parts)

        return base_name

    # 如果所有部分都被认为是版本号，则返回原名

    return name_part


if __name__ == "__main__":
    print(extract_base_name("bond-service-api-1.1.4.0.jar"))
    print(Path(FILE_LIST_TO_EXTRACT))
