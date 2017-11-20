import os
import sys

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

