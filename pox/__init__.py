import logging

LOG_FMT = "%(asctime)s.%(msecs)03d %(name)s %(module)s@%(lineno)d [%(levelname)s]: %(message)s"
LOG_DATEFMT = "%m-%d %H:%M:%S"

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter(fmt=LOG_FMT, datefmt=LOG_DATEFMT))
logger = logging.getLogger()
logger.addHandler(stream_handler)
