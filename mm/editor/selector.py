# FORMS file selector interface

import os
import fl

cwd = os.getcwd()

def selector(pathname):
	if pathname == '' or pathname == '/dev/null':
		dir, file = '', ''
		# This triggers the default of show_file_selector,
		# which is carried over from the last call.
	else:
		if pathname[-1:] == '/':
			dir, file = pathname, '.'
		else:
			dir, file = os.path.split(pathname)
		if dir == '' or dir == cwd:
			dir = '.'
	pathname = fl.show_file_selector('Select file', dir, '', file)
	if pathname == None: # user pressed 'Cancel' button
		return None
	if pathname[-1:] == '/':
		dir, file = pathname, '.'
	else:
		dir, file = os.path.split(pathname)
	if dir == cwd or dir == '.' or dir == '':
		pathname = file
	return pathname
