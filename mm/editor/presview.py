# Presentation view -- main program for testing

import sys
from MMExc import *
import MMTree
import Player
import Clist

def main():
	if sys.argv[1:]:
		filename = sys.argv[1]
	else:
		filename = 'demo.cmif'
	#
	print 'parsing...'
	root = MMTree.ReadFile(filename)
	#
	print 'make clist...'
	clist = Clist.Clist().init(root.context)
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
