# Presentation view

import sys
from MMExc import *
import MMTree
import Player

# Main program for testing

def main():
	if sys.argv[1:]:
		filename = sys.argv[1]
	else:
		filename = 'demo.cmif'
	#
	print 'parsing...'
	root = MMTree.ReadFile(filename)
	#
	print 'make player...'
	player = Player.Player().init(root)
	#
	print 'run...'
	player.run() # Never returns normally

try:
	main()
except ExitException, status:
	sys.exit(status)
