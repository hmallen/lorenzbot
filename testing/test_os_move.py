import os
import sys

test_dir = './'
test_dir_new = 'test_dir/'

test_path = './test.txt'
test_path_new = 'test_dir/test_moved.txt'

#print(os.listdir(test_dir))
print(os.listdir(test_dir_new))

os.rename(test_path, test_path_new)

#print(os.listdir(test_dir))
print(os.listdir(test_dir_new))

os.rename(test_path_new, test_path)

#print(os.listdir(test_dir))
print(os.listdir(test_dir_new))

sys.exit()
