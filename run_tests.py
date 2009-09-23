import os
import sys

DIR_PATH = os.curdir
EXTRA_PATHS = [
  DIR_PATH,
  os.path.join(DIR_PATH, 'lib'),
  os.path.join(DIR_PATH, 'test')
]

def callback( arg, dirname, fnames ):
    for file in fnames:
		fullpath = os.path.join(dirname,file)
		if os.path.isfile(fullpath):
			print "running.. " + fullpath
			execfile(fullpath, globals())

if __name__ == '__main__':
  sys.path = EXTRA_PATHS + sys.path
  print sys.path
  os.path.walk(os.path.join(DIR_PATH, 'test'),callback,[])
		