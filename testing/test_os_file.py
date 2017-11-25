import os

os.chdir('../')

test_path = 'lorenzbot.py'
test_path_fake = 'lbot.py'

test_result = os.path.isfile(test_path)
test_fake_result = os.path.isfile(test_path_fake)

print(test_result)
print(test_fake_result)
