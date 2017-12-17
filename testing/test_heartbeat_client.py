import logging
import sys
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

heartbeat_file = 'hb.txt'

time_current = time.time()
time_last = time_current


def heartbeat():
    try:
        with open(heartbeat_file, 'w') as hb:
            hb.write(str(time.time()))
        
    except Exception as e:
        logger.exception('Exception occurred while writing heartbeat to file.')
        raise


if __name__ == '__main__':
    heartbeat()
    
    while (True):
        try:
            with open(heartbeat_file, 'r') as hb:
                time_last = float(hb.read())

            time_diff = time.time() - time_last
                
            logger.info('Last heartbeat ' + "{:.2f}".format(time_diff) + ' seconds ago.')

            heartbeat()

            time.sleep(10)

        except Exception as e:
            logger.exception(e)

        except KeyboardInterrupt:
            logger.info('Exit signal received.')
            sys.exit()
