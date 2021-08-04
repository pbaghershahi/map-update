import os, argparse

parser = argparse.ArgumentParser(description="Test one")
parser.add_argument('-u', '--utm', action='store_true', default=False)
args = parser.parse_args()
print(args.utm)