import os
import shutil

test_file = './test.txt'
test_file_copy = './test_copy.txt'

try:
    new_path = shutil.copy(test_file, test_file_copy)
    print(new_path)
except:
    print('Failed to copy file.')

dir_contents = os.listdir()
print(dir_contents)

#if os.path.isfile(test_file_copy):
#    os.remove(test_file_copy)

#dir_contents = os.listdir()
#print(dir_contents)
