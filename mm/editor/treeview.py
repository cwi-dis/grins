# stand-alone tree view (prototype)

import sys
import string
from MMExc import *
import MMTree
import MMAttrdefs
import MMParser
import MMWrite
import fl
from FL import *

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
	print 'make quit button...'
	quitform = fl.make_form(FLAT_BOX, 100, 100)
	quitbutton = quitform.add_button(NORMAL_BUTTON, 5, 5, 90, 90, 'QUIT')
	#
	print 'open root...'
	root.form = opennode(root)
	#
	print 'show forms...'
	quitform.show_form(PLACE_SIZE, FALSE, 'QUIT')
	root.form.show_form(PLACE_SIZE, TRUE, 'Root node')
	#
	print 'go...'
	obj = fl.do_forms()
	if obj <> quitbutton: print 'He?'

def opennode(node):
	type = node.GetType()
	form = fl.make_form(FLAT_BOX, 400, 200)
	typebox = form.add_text(NORMAL_TEXT, 0, 150, 100, 30, type)
	if type in ('seq', 'par', 'grp'):
		x, y = 0, 0
		children = node.GetChildren()
		for i in range(len(children)):
			c = children[i]
			cbox = form.add_button(PUSH_BUTTON, \
				x, y, 50, 50, `i+1`)
			cbox.set_call_back(cbox_callback, c)
			x = x + 50
	elif type = 'imm':
		text = string.join(node.GetValues())
		vbox = form.add_text(NORMAL_TEXT, 0, 0, 400, 50, text)
	return form

def cbox_callback(object, node):
	if object.get_button():
		node.form = opennode(node)
		node.form.show_form(PLACE_SIZE, TRUE, 'Inner node')
	else:
		node.form.hide_form()

main()
