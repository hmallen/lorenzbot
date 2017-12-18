#!./env/bin/python

import argparse
import logging
import sys
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true', default=False, help='Include DEBUG level output.')
parser.add_argument('-t', '--time', type=float, required=True, help='Loop time used on heartbeat client.')
args = parser.parse_args()

debug = args.debug
if debug == False:
    logger.setLevel(level=logging.INFO)
logger.debug('[SERVER] debug: ' + str(debug))
check_time = args.time
logger.debug('[SERVER] check_time: ' + "{:.2f}".format(check_time))

heartbeat_file = 'hb.txt'


def heartbeat_check():
    try:
        with open(heartbeat_file, 'r') as hb:
            hb_time = float(hb.read())

        return hb_time

    except Exception as e:
        logger.exception('[SERVER] Exception occurred while checking heartbeat.')
        raise


if __name__ == '__main__':
    heartbeat_still_count = 0
    try:
        while (True):
            heartbeat_diff = time.time() - heartbeat_check()
            logger.debug('[SERVER] Last heartbeat ' + "{:.2f}".format(heartbeat_diff) + ' seconds ago.')

            if heartbeat_diff > check_time:
                heartbeat_still_count += 1
            else:
                heartbeat_still_count = 0

            if heartbeat_still_count >= 3:
                # Alert user of heartbeat timeout
                logger.critial('ALERT! NO HEARTBEAT DETECTED IN LAST ' + str(heartbeat_still_count) + ' CHECKS!')
                
            logger.debug('[SERVER] heartbeat_still_count: ' + str(heartbeat_still_count))

            time.sleep(check_time)

    except Exception as e:
        logger.exception(e)

    except KeyboardInterrupt:
        logger.debug('[SERVER] Exit signal received.')
        sys.exit()
