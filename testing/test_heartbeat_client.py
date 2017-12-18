import logging
import subprocess
import sys
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

heartbeat_file = 'hb.txt'
loop_time = 10

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
    try:
        # Start heartbeat server
        proc = subprocess.Popen(['python', 'test_heartbeat_server.py', '-t', str(loop_time)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        logger.debug('out: ' + out)
        logger.debug('err: ' + err)

        time.sleep(5)
        
        proc.kill()
        out, err = proc.communicate()
        logger.debug('out: ' + out)
        logger.debug('err: ' + err)

        sys.exit()

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
        sys.exit()
