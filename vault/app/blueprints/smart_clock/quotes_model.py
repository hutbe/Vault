import json
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from pathlib import Path
from typing import List, Dict, Any
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

Base = declarative_base()


class Quote(Base):
    __tablename__ = 'quotes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    creation_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    favorite = Column(Boolean, default=False)
    collections = Column(String(255), default='')
    location = Column(String(255), default='')
    source = Column(String(255), nullable=True)
    tags = Column(String(500), default='')
    authors = Column(String(255), default='')
    is_custom = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment='记录创建时间')
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment='记录时间')

    def __repr__(self):
        return f"<Quote(id={self.id}, author='{self.authors[:20]}...')>"


class QuoteImporter:
    def __init__(self, db_url: str = "sqlite:///quotes.db"):
        """初始化导入器

        Args:
            db_url: 数据库连接URL，例如：
                   - SQLite: sqlite:///quotes.db
                   - PostgreSQL: postgresql://user:password@localhost/quotes
                   - MySQL: mysql://user:password@localhost/quotes
        """
        self.db_url = db_url
        self.engine = create_engine(db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)

        # 创建表（如果不存在）
        Base.metadata.create_all(self.engine)
        logger.info(f"数据库初始化完成: {db_url}")

    def read_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """从JSON文件读取数据

        Args:
            file_path: JSON文件路径

        Returns:
            引用数据列表
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 处理不同格式的JSON数据
            if isinstance(data, list):
                quotes = data
            elif isinstance(data, dict):
                # 如果是包含quotes键的字典
                if 'quotes' in data:
                    quotes = data['quotes']
                else:
                    # 如果是单个quote对象，包装成列表
                    quotes = [data]
            else:
                raise ValueError("JSON格式不支持")

            logger.info(f"从 {file_path} 读取了 {len(quotes)} 条引用记录")
            return quotes

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            raise
        except Exception as e:
            logger.error(f"读取文件错误: {e}")
            raise

    def parse_creation_date(self, date_str: str) -> datetime.datetime:
        """解析创建日期字符串

        Args:
            date_str: 日期字符串，如 "2025-02-07T09:01:05Z"

        Returns:
            datetime对象
        """
        if not date_str:
            return None

        try:
            # 处理ISO格式的时间字符串
            date_str = date_str.replace('Z', '+00:00')
            return datetime.datetime.fromisoformat(date_str)
        except ValueError as e:
            logger.warning(f"日期解析失败 '{date_str}': {e}")
            return None

    def create_quote_object(self, quote_data: Dict[str, Any]) -> Quote:
        """从字典数据创建Quote对象

        Args:
            quote_data: 引用数据字典

        Returns:
            Quote对象
        """
        quote = Quote()

        # 处理文本内容（必填）
        if 'text' in quote_data and quote_data['text']:
            quote.text = quote_data['text']
        else:
            raise ValueError("引用文本不能为空")

        # 处理创建日期
        if 'creationDate' in quote_data:
            quote.creation_date = self.parse_creation_date(quote_data['creationDate'])

        # 处理其他字段
        quote.favorite = quote_data.get('favorite', False)
        quote.collections = str(quote_data.get('collections', '')) or ''
        quote.location = str(quote_data.get('location', '')) or ''
        quote.source = quote_data.get('source')
        quote.tags = str(quote_data.get('tags', '')) or ''
        quote.authors = str(quote_data.get('authors', '')) or ''

        return quote

    def import_quotes(self, quotes_data: List[Dict[str, Any]],
                      batch_size: int = 100) -> Dict[str, int]:
        """导入引用数据到数据库

        Args:
            quotes_data: 引用数据列表
            batch_size: 批量提交大小

        Returns:
            包含统计信息的字典
        """
        session = self.Session()
        stats = {
            'total': len(quotes_data),
            'success': 0,
            'failed': 0,
            'errors': []
        }

        try:
            for i, quote_data in enumerate(quotes_data, 1):
                try:
                    quote = self.create_quote_object(quote_data)
                    session.add(quote)

                    # 批量提交
                    if i % batch_size == 0:
                        session.commit()
                        logger.info(f"已处理 {i}/{len(quotes_data)} 条记录")

                except Exception as e:
                    stats['failed'] += 1
                    error_msg = f"第 {i} 条记录处理失败: {str(e)}"
                    stats['errors'].append(error_msg)
                    logger.error(error_msg)
                    session.rollback()  # 回滚当前事务

            # 提交剩余记录
            session.commit()
            stats['success'] = stats['total'] - stats['failed']

            logger.info(f"导入完成: 成功 {stats['success']} 条, 失败 {stats['failed']} 条")

        except Exception as e:
            session.rollback()
            logger.error(f"导入过程中发生错误: {e}")
            raise

        finally:
            session.close()

        return stats

    def validate_quotes(self, quotes_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证引用数据

        Args:
            quotes_data: 原始引用数据

        Returns:
            验证通过的引用数据
        """
        valid_quotes = []
        invalid_count = 0

        for i, quote in enumerate(quotes_data):
            # 检查必要字段
            if not quote.get('text'):
                logger.warning(f"第 {i + 1} 条记录缺少text字段，已跳过")
                invalid_count += 1
                continue

            # 清理数据
            cleaned_quote = {}
            for key, value in quote.items():
                if value is None:
                    cleaned_quote[key] = ''
                elif isinstance(value, (int, float, bool)):
                    cleaned_quote[key] = value
                else:
                    cleaned_quote[key] = str(value).strip()

            valid_quotes.append(cleaned_quote)

        if invalid_count > 0:
            logger.warning(f"跳过了 {invalid_count} 条无效记录")

        return valid_quotes

    def export_to_json(self, output_path: str = "quotes_export.json"):
        """从数据库导出数据到JSON文件

        Args:
            output_path: 输出文件路径
        """
        session = self.Session()

        try:
            quotes = session.query(Quote).all()
            data = []

            for quote in quotes:
                quote_dict = {
                    "creationDate": quote.creation_date.isoformat() if quote.creation_date else None,
                    "favorite": quote.favorite,
                    "collections": quote.collections,
                    "location": quote.location,
                    "source": quote.source,
                    "text": quote.text,
                    "tags": quote.tags,
                    "authors": quote.authors
                }
                data.append(quote_dict)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"已导出 {len(quotes)} 条记录到 {output_path}")

        finally:
            session.close()


def main():
    """主函数"""
    # 配置
    JSON_FILE = "Quotes.json"  # 你的JSON文件路径
    DB_URL = "mysql+pymysql://hut:hut123456@127.0.0.1:3306/home_db"  # 数据库URL

    try:
        # 创建导入器
        importer = QuoteImporter(DB_URL)

        # 读取JSON文件
        logger.info(f"开始读取文件: {JSON_FILE}")
        raw_quotes = importer.read_json_file(JSON_FILE)

        # 验证数据
        logger.info("开始验证数据...")
        valid_quotes = importer.validate_quotes(raw_quotes)

        if not valid_quotes:
            logger.error("没有有效数据可以导入")
            return

        # 导入数据
        logger.info("开始导入数据到数据库...")
        stats = importer.import_quotes(valid_quotes)

        # 显示统计信息
        print("\n" + "=" * 50)
        print("导入统计:")
        print(f"总记录数: {stats['total']}")
        print(f"成功导入: {stats['success']}")
        print(f"导入失败: {stats['failed']}")

        if stats['errors']:
            print("\n错误详情:")
            for error in stats['errors'][:10]:  # 只显示前10个错误
                print(f"  - {error}")
            if len(stats['errors']) > 10:
                print(f"  ... 还有 {len(stats['errors']) - 10} 个错误")

        print("=" * 50)

        # 可选：导出备份
        # importer.export_to_json("quotes_backup.json")

    except FileNotFoundError as e:
        logger.error(f"文件错误: {e}")
        print(f"请确保文件 '{JSON_FILE}' 存在")
    except json.JSONDecodeError as e:
        logger.error(f"JSON格式错误: {e}")
        print(f"文件 '{JSON_FILE}' 不是有效的JSON格式")
    except Exception as e:
        logger.error(f"导入失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()