import mimetypes
import os
from typing import List, Dict
from config.settings import BASE_DIR


def get_file_type(file_path: str) -> str:
    """
    获取文件类型
    Args:
        file_path: 文件路径
    Returns:
        str: 文件类型描述
    """
    # 初始化mimetypes
    mimetypes.init()
    # 获取MIME类型
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        # 如果无法检测到MIME类型，则返回文件扩展名
        ext = os.path.splitext(file_path)[1][1:].lower()
        return ext if ext else "unknown"
    return mime_type


def inspect_test_files() -> List[Dict]:
    """
    获取data/files目录下的文件信息
    Returns:
        List[Dict]: 包含文件名、文件路径和文件类型的列表
    """
    file_info_list = []
    file_dir = os.path.join(BASE_DIR, 'datas', 'files')

    # 确保目录存在
    if not os.path.exists(file_dir):
        os.makedirs(file_dir, exist_ok=True)
        return file_info_list

    # 遍历目录下的所有文件
    for file_name in os.listdir(file_dir):
        file_path = os.path.join(file_dir, file_name)
        if os.path.isfile(file_path):  # 只处理文件，不处理子目录
            file_info = {
                "file_name": file_name,
                "file_path": file_path,
                "file_type": get_file_type(file_path)
            }
            file_info_list.append(file_info)

    return file_info_list
