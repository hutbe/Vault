# 自动发现并注册本包下每个子包（或子模块）中的蓝图
# 约定：每个子包或模块在其 api.py 或 __init__.py 中导出名为 `bp`（或 `blueprint`）的 Blueprint 实例

from loguru import logger
from importlib import import_module
from pkgutil import iter_modules
import sys


def register_blueprints(app):
    """
    自动扫描 app.blueprints 包下的子模块/子包，尝试导入 `{package}.{name}.api`
    或 `{package}.{name}`，寻找名为 `bp` 或 `blueprint` 的对象并注册到 app。

    用法（在你的 create_app 工厂中）:
        from app.blueprints import register_blueprints
        register_blueprints(app)
    """
    package = __name__  # "app.blueprints"
    base_path = __path__[0] if hasattr(__path__, '__getitem__') else __path__._path[0]

    logger.info(f"开始扫描蓝图，包路径: {base_path}")

    for finder, name, ispkg in iter_modules(__path__):
        logger.debug(f"处理模块: {name}, 是否是包: {ispkg}")

        # 跳过以 _ 开头的模块（如 __pycache__ 等）
        if name.startswith('_'):
            continue

        loaded = False
        bp_instance = None
        module_used = None

        # 根据是否是包来决定尝试的导入路径
        if ispkg:
            # 对于包，先尝试导入 package.name.api，再尝试 package.name
            candidates = [f"{package}.{name}.api", f"{package}.{name}"]
        else:
            # 对于普通模块，直接导入
            candidates = [f"{package}.{name}"]

        for modname in candidates:
            try:
                logger.debug(f"尝试导入: {modname}")
                mod = import_module(modname)

                # 查找蓝图实例
                for attr_name in ("bp", "blueprint"):
                    bp_candidate = getattr(mod, attr_name, None)
                    if bp_candidate is not None:
                        # 检查是否是 Blueprint 实例
                        if hasattr(bp_candidate, 'register') or hasattr(bp_candidate, 'add_url_rule'):
                            bp_instance = bp_candidate
                            module_used = modname
                            logger.info(f"找到蓝图 {attr_name} 在 {modname}")
                            break

                if bp_instance is not None:
                    break

            except ImportError as e:
                logger.debug(f"导入失败 {modname}: {e}")
                continue
            except Exception as e:
                logger.warning(f"导入模块 {modname} 时出现意外错误: {e}")
                continue

        # 注册找到的蓝图
        if bp_instance is not None:
            try:
                app.register_blueprint(bp_instance)
                bp_name = getattr(bp_instance, 'name', '未知名称')
                logger.info(f"已注册蓝图: {bp_name} (来自 {module_used})")
                loaded = True
            except Exception as e:
                logger.error(f"注册蓝图失败 {module_used}: {e}")
        else:
            logger.warning(f"在 {name} 中未找到蓝图 (尝试过: {candidates})")

    # 记录最终的蓝图信息
    registered_blueprints = list(app.blueprints.keys())
    logger.info(f"蓝图注册完成。已注册的蓝图: {registered_blueprints}")


# 可选：提供一个手动注册特定蓝图的方法
def register_blueprint_manually(app, blueprint_module_path):
    """
    手动注册指定模块路径的蓝图
    """
    try:
        mod = import_module(blueprint_module_path)
        for attr_name in ("bp", "blueprint"):
            bp = getattr(mod, attr_name, None)
            if bp is not None:
                app.register_blueprint(bp)
                logger.info(f"手动注册蓝图: {getattr(bp, 'name', '未知名称')} (来自 {blueprint_module_path})")
                return True
        logger.warning(f"在 {blueprint_module_path} 中未找到蓝图")
        return False
    except Exception as e:
        logger.error(f"手动注册蓝图失败 {blueprint_module_path}: {e}")
        return False