import argparse
import logging
import sys
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--time', type=float, required=True, help='Loop time used on heartbeat client.')
args = parser.parse_args()

check_time = args.time
logger.debug('check_time: ' + "{:.2f}".format(check_time))

heartbeat_file = 'hb.txt'


def heartbeat_check():
    try:
        with open(heartbeat_file, 'r') as hb:
            hb_time = float(hb.read())

        return hb_time

    except Exception as e:
        logger.exception('Exception occurred while checking heartbeat.')
        raise


if __name__ == '__main__':
    heartbeat_still_count = 0
    try:
        while (True):
            heartbeat_diff = time.time() - heartbeat_check()
            logger.info('Last heartbeat ' + "{:.2f}".format(heartbeat_diff) + ' seconds ago.')

            if heartbeat_diff > check_time:
                heartbeat_still_count += 1
            else:
                heartbeat_still_count = 0

            if heartbeat_still_count >= 3:
                logger.error('Heartbeat not detected for at least 3 checks.')
                # Put some alert system here
                
            logger.debug('heartbeat_still_count: ' + str(heartbeat_still_count))

            time.sleep(check_time)

    except Exception as e:
        logger.exception(e)

    except KeyboardInterrupt:
        logger.info('Exit signal received.')
        sys.exit()
