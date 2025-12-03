import re
from flask import request, has_request_context

def get_param(name, default=None, type_=int):
    """更安全的实现，带上下文检查"""
    if not has_request_context():
        return default

    value = None
    if name in request.args:
        value = request.args.get(name)
    elif request.is_json:
        data = request.get_json() or {}
        value = data.get(name)
    elif name in request.form:
        value = request.form.get(name)

    if value is None:
        return default

    if type_:
        try:
            if type_ == bool:
                return value.lower() in ('true', '1', 'yes', 'on') if isinstance(value, str) else bool(value)
            elif type_ == float:
                temp = float(re.sub(r'[^\d.]+', '', value))
            return type_(value)
        except (ValueError, TypeError):
            return default

    return value

def get_value_from_request_params_without_error(req, key):
    result, error = get_value_from_request_params(req, key)
    return result

def get_value_from_request_params(req, key):
    params = get_request_parameters(req)
    """
    从参数字典中安全获取参数
    """
    # 使用 get() 并检查空值
    value_for_key = params.get(key)

    if value_for_key is None:
        return None, "参数不存在"

    if not value_for_key:
        return None, "值存在但为空"

    return value_for_key, None

def get_request_parameters(req):
    """
    统一获取请求参数

    Args:
        req: Flask请求对象

    Returns:
        dict: 参数字典
    """
    content_type = req.content_type or ''
    data = {}

    try:
        # 处理 JSON 类型请求
        if content_type.startswith('application/json'):
            raw_data = req.get_data(as_text=True)
            if raw_data.strip():  # 确保不是空字符串
                data = req.get_json(force=True, silent=True) or {}
            return data

        # 处理表单编码和查询参数
        elif (content_type.startswith('application/x-www-form-urlencoded') or
              content_type.startswith('multipart/form-data')):

            # 合并查询参数和表单数据
            if req.args:
                data.update(req.args.to_dict())
            if req.form:
                data = _process_form_data(req, data)  # 修正：传递data参数

            return data

        # 处理其他内容类型或空内容类型
        else:
            if req.args:
                data.update(req.args.to_dict())
            return data

    except Exception as e:
        print(f"获取请求参数时出错: {e}")
        return {}


def _process_form_data(req, data):
    """
    处理表单数据，支持数组字段

    Args:
        req: 请求对象
        data: 数据字典

    Returns:
        dict: 处理后的数据字典
    """
    for key, value in req.form.items():
        # 处理数组字段 (如: key[])
        if key.endswith('[]'):
            array_key = key[:-2]
            data[array_key] = req.form.getlist(key)
        else:
            # 如果字段已存在（来自查询参数），且当前是数组值，则转换为数组
            if key in data and isinstance(req.form.getlist(key), list) and len(req.form.getlist(key)) > 1:
                data[key] = req.form.getlist(key)
            else:
                data[key] = value

    # 处理文件上传
    if req.files:
        data = _process_files_data(req, data)  # 修正：传递data参数

    return data


def _process_files_data(req, data):
    """
    处理文件上传数据

    Args:
        req: 请求对象
        data: 数据字典

    Returns:
        dict: 包含文件数据的字典
    """
    for key in req.files:
        files = req.files.getlist(key)
        if len(files) == 1:
            data[key] = files[0]  # 单个文件
        else:
            data[key] = files  # 多个文件
    return data
