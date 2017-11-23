import sys
import time


def test_fxn(trade_amount=None):
    if not trade_amount:
        print('NOT trade_amount')
    else:
        print('trade_amount')


if __name__ == '__main__':
    test_fxn()
    time.sleep(3)
    test_fxn(1)
    time.sleep(3)
    test_fxn()
    time.sleep(3)
    test_fxn(2)
    time.sleep(3)
    sys.exit()
