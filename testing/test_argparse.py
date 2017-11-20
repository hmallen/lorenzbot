import argparse

parser = argparse.ArgumentParser(description='Test description.')
parser.add_argument('-c', '--clean', action='store_true')
args = parser.parse_args()
clean_coll = args.clean

print(args)
print(clean_coll)
