import hashlib

def allowed_file(filename, allowed_extensions):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions

def calculate_partial_md5_flexible(file_path, bytes_to_read=512 * 1024):
    """计算文件前指定字节数的 MD5"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        # 读取指定字节数
        data = f.read(bytes_to_read)
        hash_md5.update(data)

    return hash_md5.hexdigest()

def calculate_fileobject_md5(file_object, chunk_size=64 * 1024):
    """
    计算文件对象前64KB的MD5值
    Args:
        file_object: Flask request.files 中的文件对象
        chunk_size: 读取的字节数，默认 64KB (65536 bytes)

    Returns:
        str: MD5哈希值（十六进制字符串）
    """
    # 保存当前文件指针位置
    current_position = file_object.tell()
    # 移动到文件开头
    file_object.seek(0)
    # 创建MD5对象
    md5_hash = hashlib.md5()
    # 只读取前64KB
    chunk = file_object.read(chunk_size)
    md5_hash.update(chunk)
    # 恢复文件指针到原来的位置（重要！）
    file_object.seek(current_position)
    return md5_hash.hexdigest()