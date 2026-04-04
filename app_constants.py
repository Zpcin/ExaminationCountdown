import os

# 数据与兼容版本号
VERSION = "build9"
DEFAULT_WATERMARK_COLOR = "#201f1e"
DEFAULT_VISIBLE_COLOR = "#0f1419"

# 配置文件路径：保存在用户主目录下，避免程序目录无写入权限
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".countdown")
CONFIG_FILE = os.path.join(CONFIG_DIR, "countdown_config.json")


def ensureConfigDir():
    """确保配置目录存在。"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
