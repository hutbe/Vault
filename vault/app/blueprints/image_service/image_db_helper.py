from PIL import Image as PILImage
from .image_db import session, Image, Base, engine, ImageType
from sqlalchemy.orm import joinedload
import os

class ImageDBHelper:
    IMAGE_PAGE_SIZE = 50  # 默认每页记录数

    @staticmethod
    def check_image_duplicate(image_md5):
        """检查文件是否重复"""
        existing_image = session.query(Image).filter_by(md5_hash=image_md5).first()
        return existing_image or None

    # 录创建缩略图-指定目标目
    @staticmethod
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

    @staticmethod
    def paginate_query(query, page=1, page_size=IMAGE_PAGE_SIZE):
        """通用的分页函数"""
        if page < 1:
            page = 1

        offset_val = (page - 1) * page_size

        # 获取总数
        total = query.count()

        # 获取分页数据
        items = query.offset(offset_val).limit(page_size).all()

        return {
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size,
            'has_prev': page > 1,
            'has_next': page < (total + page_size - 1) // page_size
        }

    @staticmethod
    def get_image_list(page=1, page_size=IMAGE_PAGE_SIZE, type_id=None, search_keyword=None):
        page = page if page is not None else 1
        page_size = page_size if page_size is not None else ImageDBHelper.IMAGE_PAGE_SIZE

        """获取图片列表（带分页和过滤）"""
        # 构建查询
        query = session.query(Image) \
            .options(joinedload(Image.image_type)) \
            .order_by(Image.id.desc())

        # 添加过滤条件
        if type_id:
            query = query.filter(Image.type_id == type_id)

        if search_keyword:
            query = query.filter(Image.original_filename.contains(search_keyword))

        # 分页
        pagination_result = ImageDBHelper.paginate_query(query, page, page_size)

        # 格式化返回数据
        formatted_items = []
        for img in pagination_result['items']:
            formatted_items.append(img.to_dict())
        return {
            'data': formatted_items,
            'pagination': {
                'current_page': pagination_result['page'],
                'page_size': pagination_result['page_size'],
                'total': pagination_result['total'],
                'pages': pagination_result['pages'],
                'has_prev': pagination_result['has_prev'],
                'has_next': pagination_result['has_next']
            }
        }

if __name__ == "__main__":
    # ImageDBHelper.get_image_list()
    #
    # # 使用示例
    # # 构建基础查询
    # base_query = session.query(Image) \
    #     .options(joinedload(Image.image_type)) \
    #     .order_by(Image.created_at.desc())
    #
    # # 添加过滤条件（可选）
    # if some_condition:
    #     base_query = base_query.filter(Image.type_id == 1)
    #
    # # 分页查询
    # result = paginate_query(base_query, page=1, page_size=15)
    #
    # for image in result['items']:
    #     print(f"ID: {image.id}, 文件名: {image.original_filename}")
    #     print(f"类型: {image.image_type.type_name}")


    # 使用
    result = ImageDBHelper.get_image_list(page=1, page_size=10, type_id=20)
    print(result)