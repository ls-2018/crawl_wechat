from logging import Logger
import logging

xxx = None


def get_logger():
    global xxx
    if xxx is not None:
        return xxx
    # 创建一个logger
    logger = logging.getLogger("wechat")

    # 设置全局日志级别为DEBUG
    logger.setLevel(logging.DEBUG)

    # 创建一个handler，用于写入日志文件
    fh = logging.FileHandler('/tmp/wechat.log',encoding='utf8')

    # 再创建一个handler，用于输出到控制台
    ch = logging.StreamHandler()

    # 定义handler的输出格式
    formatter = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)d - %(name)s - %(levelname)s - %(message)s ')

    # 给handler设置输出格式
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # 给logger添加handler
    logger.addHandler(fh)
    logger.addHandler(ch)

    # 记录一条日志
    # logger.debug('This is a debug message')
    # logger.info('This is an info message')
    # logger.warning('This is a warning message')
    # logger.error('This is an error message')
    # logger.critical('This is a critical message')
    Logger.manager.loggerDict['werkzeug'] = logger
    xxx = logger
    return logger
