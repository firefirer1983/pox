import logging
import sys


def pytest_configure(config):
    # 设置 root logger，写到 stderr
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)
