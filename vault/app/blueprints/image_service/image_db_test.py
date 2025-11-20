

# Run tests with: python -m unittest <filename>

# python -m unittest models.image_db_test 使用模块化运行测试


import unittest
from .image_db import db_manager, Image
import os
from werkzeug.utils import secure_filename
import uuid
import hashlib

from .image_db_helper import ImageDBHelper


def get_image(filename):
    """通过UUID文件名获取图片"""
    # 检查数据库中是否存在且未删除
    file_on_disk_name = filename
    with db_manager.session_scope() as session:
        image = session.query(Image).filter_by(
            uuid_filename=filename,
            is_deleted=False
        ).first()

        if image is None:
            # 尝试通过原始文件名查找-不推荐，可能有重复
            image = session.query(Image).filter_by(
                original_filename=filename,
                is_deleted=False
            ).first()
        file_on_disk_name = image.uuid_filename if image else None

    if not image:
        print("Image not found filename:", filename)
        return None
    if not image.image_type:
        print("No image type associated")
    return image

class ImageDBTestCase(unittest.TestCase):
    # def test_create_image(self):
    #     """通过UUID文件名获取图片"""
    #     # 检查数据库中是否存在且未删除
    #     test_file_name = '143a1547183f4e0eb8cb2869c30b549e.jpg'
    #     file_on_disk_name = ''
    #     image = session.query(Image).filter_by(
    #         uuid_filename=test_file_name,
    #         is_deleted=False
    #     ).first()
    #
    #     if image is None:
    #         # 尝试通过原始文件名查找-不推荐，可能有重复
    #         image = session.query(Image).filter_by(
    #             original_filename=test_file_name,
    #             is_deleted=False
    #         ).first()
    #         file_on_disk_name = image.uuid_filename if image else None
    #     self.assertIsNotNone(image)
    #     self.assertIsNotNone(image.image_type)
    #     new_image_dict = image.to_dict()
    #     self.assertIsNotNone(new_image_dict)
    #     self.assertEqual(new_image_dict['url'], "/images/10_douban_movie/143a1547183f4e0eb8cb2869c30b549e.jpg")

    # def test_paginate_query(self):
    #     """测试分页查询功能"""
    #     query = session.query(Image).order_by(Image.id.desc())
    #     page = 1
    #     page_size = 5
    #     pagination_result = ImageDBHelper.paginate_query(query, page, page_size)
    #
    #     self.assertIn('items', pagination_result)
    #     self.assertIn('total', pagination_result)
    #     self.assertIn('page', pagination_result)
    #     self.assertIn('page_size', pagination_result)
    #     self.assertIn('pages', pagination_result)
    #     self.assertIn('has_prev', pagination_result)
    #     self.assertIn('has_next', pagination_result)
    #
    #     self.assertEqual(pagination_result['page'], page)
    #     self.assertEqual(pagination_result['page_size'], page_size)
    #     self.assertLessEqual(len(pagination_result['items']), page_size)

    def test_get_image_list(self):
        """测试获取图片列表功能"""
        result = ImageDBHelper.get_image_list(page=1, page_size=3, type_id=20)

        print("========== xxxxxx result: ", result);

        self.assertIn('data', result)
        self.assertIn('pagination', result)

        self.assertIsInstance(result['data'], list)
        self.assertIn('current_page', result['pagination'])
        self.assertIn('page_size', result['pagination'])
        self.assertIn('total', result['pagination'])
        self.assertIn('pages', result['pagination'])
        self.assertIn('has_prev', result['pagination'])
        self.assertIn('has_next', result['pagination'])

        self.assertEqual(result['pagination']['current_page'], 1)
        self.assertEqual(result['pagination']['page_size'], 3)
        self.assertLessEqual(len(result['data']), 3)

# python -m unittest models/image_db_test.py
if __name__ == "__main__":
    unittest.main()

    # img = get_image('0a6429c70f89488ca5f7c0c43ae4da53.jpg')
    #
    # if img:
    #     print(img.to_dict())
    #     if img.image_type:
    #         print(f"Image type: {img.image_type.to_dict()}")
    #         type_id_type_name = f"{img.image_type.type_id}_{img.image_type.type_name}"
    #         print(type_id_type_name)
    #
    #         BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    #         IMAGE_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    #         filepath = os.path.join(IMAGE_UPLOAD_FOLDER, type_id_type_name, img.uuid_filename)