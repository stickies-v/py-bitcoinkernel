#!/opt/homebrew/bin/python3

# Copied from https://github.com/trolldbois/ctypeslib/issues/125#issuecomment-1552170404
import sys
import os

args = sys.argv[1:]
args.remove("--dynamic")
# print(args, file=sys.stderr)
os.execvp("nm", args)
