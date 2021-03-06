import argparse
import logging
import subprocess
import sys
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true', default=False, help='Include DEBUG level output.')
parser.add_argument('--notelegram', action='store_true', default=False, help='Disable Telegram alerts.')
args = parser.parse_args()

debug = args.debug
if debug == False:
    logger.setLevel(level=logging.INFO)
logger.debug('debug: ' + str(debug))

telegram_disable = args.notelegram

heartbeat_file = 'hb.txt'
loop_time = 10


def heartbeat():
    try:
        with open(heartbeat_file, 'w') as hb:
            hb.write(str(time.time()))
        
    except Exception as e:
        logger.exception('Exception occurred while writing heartbeat to file.')
        raise


if __name__ == '__main__':
    time_last = time.time() - 900
    try:
        # Start heartbeat server
        proc_list = []
        proc_list.append('./test_heartbeat_server.py')

        proc_list.append('-t')
        proc_list.append(str(loop_time))

        if debug == True:
            proc_list.append('-d')

        if telegram_disable == True:
            proc_list.append('--notelegram')

        proc = subprocess.Popen(proc_list)
        
        #if debug == False:
            #proc = subprocess.Popen(['./test_heartbeat_server.py', '-t', str(loop_time)])
        #else:
            #proc = subprocess.Popen(['./test_heartbeat_server.py', '-t', str(loop_time), '-d'])

        # Write initial heartbeat to file
        heartbeat()
    
        while (True):
            with open(heartbeat_file, 'r') as hb:
                time_last = float(hb.read())

            time_diff = time.time() - time_last
                
            logger.info('Last heartbeat ' + "{:.2f}".format(time_diff) + ' seconds ago.')

            heartbeat()

            time.sleep(loop_time)

    except Exception as e:
        logger.exception(e)

    except KeyboardInterrupt:
        logger.info('Exit signal received.')
        proc.kill()
        sys.exit()
