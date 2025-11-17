import requests
import os
from pathlib import Path

# 使用单个文件上传的接口，逐个上传图片
def batch_upload_images(folder_path, upload_url):
    """批量上传目录下的所有图片"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

    for file_path in Path(folder_path).iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            try:
                with open(file_path, 'rb') as f:
                    files = {'file': (file_path.name, f, 'image/jpeg')}
                    params = {'type_id': 22, 'tags': 'screenshot'}
                    response = requests.post(upload_url, data=params, files=files)

                    print(f"上传 {file_path.name}: {response.status_code}")
                    if response.status_code == 200:
                        print(f"成功: {response.json()}")
                    else:
                        print(f"失败: {response.text}")

            except Exception as e:
                print(f"上传 {file_path.name} 时出错: {e}")

# 使用多个文件上传的接口，每次上传多个图片
def batch_upload_multiple_images(folder_path, upload_url, batch_size=5):
    """分批上传图片，每批上传多个文件"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

    # 收集所有文件
    all_files = []
    for file_path in Path(folder_path).iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            all_files.append(file_path)

    if not all_files:
        print("没有找到可上传的图片文件")
        return

    # 分批处理
    for i in range(0, len(all_files), batch_size):
        batch_files = all_files[i:i + batch_size]
        print(f"上传第 {i // batch_size + 1} 批，共 {len(batch_files)} 个文件")

        # 准备当前批次的文件
        files = []
        for file_path in batch_files:
            files.append(('file', (file_path.name, open(file_path, 'rb'), 'image/jpeg')))

        # 上传当前批次
        try:
            params = {'type_id': 22, 'tags': f'batch_{i // batch_size + 1}'}
            response = requests.post(upload_url, data=params, files=files)

            print(f"第 {i // batch_size + 1} 批上传结果: {response.status_code}")
            if response.status_code == 200:
                print(f"成功: {response.json()}")
            else:
                print(f"失败: {response.text}")

        except Exception as e:
            print(f"第 {i // batch_size + 1} 批上传时出错: {e}")
        finally:
            # 关闭当前批次的所有文件
            for file_tuple in files:
                file_tuple[1][1].close()

# 使用示例
if __name__ == "__main__":
    batch_upload_images('./to_upload_images', 'http://20.4.2.128:8090//images/upload')
    # batch_upload_multiple_images('./to_upload_images', 'http://127.0.0.1:5002/images/multiple_upload', 2)

"""
#!/bin/bash

UPLOAD_URL="http://localhost:5000/upload"
IMAGE_DIR="/path/to/your/images"

for file in "$IMAGE_DIR"/*.{jpg,jpeg,png,gif}; do
    if [ -f "$file" ]; then
        echo "上传: $(basename "$file")"
        curl -X POST "$UPLOAD_URL" \
             -F "file=@$file" \
             -s -o response.json
        
        echo "状态: $(jq '.success' response.json 2>/dev/null || cat response.json)"
        echo "---"
    fi
done
"""