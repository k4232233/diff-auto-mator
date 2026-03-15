"""
@Author：haoran.xu
"""


def generate_file_list(data):
    """
    处理输入数据，生成完整的文件路径列表。
    """
    file_paths = []

    lines = data.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split('\t')

        if len(parts) >= 2:
            file_name = parts[0].strip()
            path_segment = parts[1].strip()

            if '$' in file_name:
                continue

            final_path = path_segment + '\\' + file_name
            file_paths.append(final_path)

    return file_paths


# if __name__ == "__main__":
#
#     INPUT_FILENAME = input(f"请输入数据源文件路径: ")
#     clean_path = INPUT_FILENAME.strip().replace('"', '')
#     # 尝试从输入文件读取数据
#     try:
#         with open(clean_path, 'r', encoding='utf-8') as f:
#             input_content = f.read()
#     except FileNotFoundError:
#         print(f"错误：找不到输入文件 '{INPUT_FILENAME}'。")
#         exit(1) # 退出程序
#
#     except Exception as e:
#         print(f"读取文件 '{INPUT_FILENAME}' 时发生错误: {e}")
#         exit(1)
#
#     # 生成路径列表
#     result_paths = generate_file_list(input_content)
#
#     # 将结果写入输出文件
#     try:
#         with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
#             # 写入时使用换行符分隔每个路径
#             f.write('\n'.join(result_paths))
#         print(f"\n成功生成文件列表，已保存到: {OUTPUT_FILENAME}")
#
#     except Exception as e:
#         print(f"写入文件时发生错误: {e}")

    # # 打印最终生成的内容以供预览
    # print("\n--- 生成的文件内容预览 ---")
    # print('\n'.join(result_paths))