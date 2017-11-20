import configparser
import os
import sys

live_trading = True

config = configparser.ConfigParser()

os.chdir('../') # Move from testing directory back to root directory
directory = os.listdir()

ini = None
for file in directory:
    print(file)
    if file.endswith('.ini'):
        ini = str(file)

if not ini:
    print('Not found.')
else:
    config_file = ini
    print()
    print('Config: ' + config_file)

print()
config.read(config_file)
sec = config.sections()
print(sec)

print()
if live_trading == False:
    print('VIEW ONLY')
    api_key = config['view']['key']
    api_secret = config['view']['secret']
else:
    print('LIVE MODE')
    api_key = config['live']['key']
    api_secret = config['live']['secret']

print('api_key: ' + api_key)
print('api_secret: ' + api_secret)
