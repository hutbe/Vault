from PIL import Image as PILImage
from image_db import session, Image, Base, engine, ImageType
import os, shutil
from werkzeug.utils import secure_filename
import uuid
import hashlib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
# 图片服务配置
IMAGE_URL_PREFIX = '/images'
THUMBNAIL_SIZE = (300, 300)

def check_image_duplicate(image_md5):
    """检查文件是否重复"""
    existing_image = session.query(Image).filter_by(md5_hash=image_md5).first()
    return existing_image or None

def calculate_partial_md5_flexible(file_path, bytes_to_read=512 * 1024):
    """计算文件前指定字节数的 MD5"""
    hash_md5 = hashlib.md5()

    with open(file_path, "rb") as f:
        # 读取指定字节数
        data = f.read(bytes_to_read)
        hash_md5.update(data)

    return hash_md5.hexdigest()

# 不同大小的测试
# small_check = calculate_partial_md5_flexible("image.jpg", 512 * 1024)  # 前64KB

def init_db():
    # 创建所有表
    Base.metadata.create_all(engine)

    # 或者删除所有表重新创建
    # Base.metadata.drop_all(engine)
    # Base.metadata.create_all(engine)


IMAGE_TYPES = [
    ImageType(
        type_id=0,
        type_name="others",
        description="未知类型的图片",
    ),
    ImageType(
        type_id=10,
        type_name="douban_movie",
        description="豆瓣上拉取的电影图片",
    ),
    ImageType(
        type_id=22,
        type_name="GreatAutumn",
        description="与刘大秋相关的图片",
    )
]

def add_image_types():
    # 生成应的目录
    for img_type in IMAGE_TYPES:
        session.add(img_type)
        directory = os.path.join(UPLOAD_FOLDER, f"{img_type.type_id}_{img_type.type_name}")
        os.makedirs(directory, exist_ok=True)
    session.commit()

def create_thumbnail(image_path, thumbnail_dir, size=(300, 300)):
    """创建缩略图在本目录"""
    # 创建缩略图目录
    """
    thumbnail_dir = os.path.join(os.path.dirname(image_path), 'thumbnails')
    os.makedirs(thumbnail_dir, exist_ok=True)

    # 生成缩略图路径
    filename = os.path.basename(image_path)
    thumbnail_path = os.path.join(thumbnail_dir, filename)
    """

    """创建缩略图在目标目录"""
    thumbnail_dir = os.path.join(thumbnail_dir, 'thumbnails')
    os.makedirs(thumbnail_dir, exist_ok=True)
    filename = os.path.basename(image_path)
    thumbnail_path = os.path.join(thumbnail_dir, filename)

    # 创建缩略图
    with PILImage.open(image_path) as img:
        img.thumbnail(size, PILImage.Resampling.LANCZOS)
        try:
            img.save(thumbnail_path, optimize=True, quality=85)
            print(f"创建缩略图成功: {thumbnail_path}")
        except Exception as e:
            print(f"创建缩略图时出错: {e}")
            return False
    return thumbnail_path

def move_file_os(source_path, destination_path):
    """使用os.rename移动文件"""
    try:
        # 确保目标目录存在
        dest_dir = os.path.dirname(destination_path)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        # 移动文件
        # os.rename(source_path, destination_path)
        # 复制文件
        shutil.copy(source_path, destination_path)

        # print(f"文件已从 {source_path} 移动或者复制到 {destination_path}")
        return True
    except FileNotFoundError:
        print(f"源文件 {source_path} 不存在")
        return False
    except Exception as e:
        print(f"移动文件时出错: {e}")
        return False

def normalize_filename(filename):
    """将文件名后缀转为小写"""
    name, ext = os.path.splitext(filename)
    return name + ext.lower()

def import_images_in_folder(image_type_id, folder_path):
    """导入指定文件夹中的所有图片到数据库"""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
    for filename in os.listdir(folder_path):
        normalized_name = normalize_filename(filename)
        if any(normalized_name.endswith(ext) for ext in allowed_extensions):
            filepath = os.path.join(folder_path, normalized_name)
            import_image(image_type_id, normalized_name, filepath)

def import_image(image_type_id, filename, origin_filepath):
    try:
        # 生成唯一文件名
        image_type_name = None
        # 生成应的目录
        for img_type in IMAGE_TYPES:
            if img_type.type_id == image_type_id:
                image_type_name = img_type.type_name
                break

        if image_type_name is None:
            print(f"导入图片时，图片类型ID未设置或是未知的类型: {image_type_id} 详见IMAGE_TYPES类型列表")
            return

        ext = os.path.splitext(secure_filename(filename))[1]
        uuid_filename = f"{uuid.uuid4().hex}{ext}"
        image_folder = f"{image_type_id}_{image_type_name}"
        filepath = os.path.join(UPLOAD_FOLDER, image_folder, uuid_filename)
        # 保存原图
        move_file_os(origin_filepath, filepath)

        # 获取图片信息
        file_size = os.path.getsize(filepath)
        small_check_md5 = calculate_partial_md5_flexible(filepath, 512 * 1024)  # 前64KB
        width, height = None, None

        try:
            with PILImage.open(filepath) as img:
                width, height = img.size
        except Exception as e:
            print(f"Cannot get image dimensions: {e}")

        # 创建缩略图
        try:
            create_thumbnail(filepath, UPLOAD_FOLDER, THUMBNAIL_SIZE)
        except Exception as e:
            print(f"Failed to create thumbnail: {e}")

        origin_filename = os.path.basename(origin_filepath)

        # 保存到数据库
        image = Image(
            type_id = 10,  # douban_movie
            uuid_filename=uuid_filename,
            original_filename=origin_filename,
            file_size=file_size,
            md5_hash=small_check_md5,
            mime_type="image/jpeg", # image/png
            width=width,
            height=height,
            description='',  # 可选描述
            tags='movie_douban'  # 可选标签
        )

        session.add(image)
        session.commit()

        # print(f"处理图片成功 原始名称: {origin_filename} UUID名称: {uuid_filename} 文件大小: {file_size} 宽度: {width} 高度: {height}")

    except Exception as e:
        print(f"处理图片失败: {e}")

if __name__ == "__main__":
    # 要在项目根目录下运行此脚本

    init_db()
    # 初始化 image type 表
    add_image_types()

    # 导入指定文件夹中的图片
    # import_images_in_folder(image_type_id=10, folder_path='./to_import_images')