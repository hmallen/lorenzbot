import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

a = float(1)
b = float(0)


def ex_function():
    try:
        c = a / b
        return c
    except Exception as e:
        logger.debug('FXN')
        logger.debug(e)
        raise


if __name__ == '__main__':
    try:
        logger.debug('Start')
        val = ex_function()
    except Exception as f:
        logger.debug('MAIN')
        logger.debug(f)
