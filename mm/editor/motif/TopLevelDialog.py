__version__ = "$Id$"

import windowinterface, WMEVENTS
from usercmd import *

class TopLevelDialog:
	adornments = {
		'toolbar': [
			('Play', PLAY),
			('Player', PLAYERVIEW, 't'),
			('Structure view', HIERARCHYVIEW, 't'),
			('Timeline view', CHANNELVIEW, 't'),
			('Layout view', LAYOUTVIEW, 't'),
			('Hyperlinks', LINKVIEW, 't'),
			('User groups', USERGROUPVIEW, 't'),
			('Properties...', PROPERTIES),
			('Source...', SOURCE),
			('Edit Source...', EDITSOURCE),
			('Save', SAVE),
			('Save as...', SAVE_AS),
			('Export...', EXPORT_SMIL),
			('Restore', RESTORE),
			('Close', CLOSE),
			('Help', HELP),
			],
		'toolbarvertical': 1,
		'close': [ CLOSE, ],
		}

	def __init__(self):
		pass

	def show(self):
		if self.window is not None:
			return
		self.window = w = windowinterface.newcmwindow(None, None, 0, 0,
				self.basename, adornments = self.adornments,
				commandlist = self.commandlist)

	def hide(self):
		if self.window is None:
			return
		self.window.close()
		self.window = None

	def setbuttonstate(self, command, showing):
		self.window.set_toggle(command, showing)

	def showsource(self, source):
		if self.source is not None and not self.source.is_closed():
			self.source._children[1].settext(source)
			self.source.show()
			return
		self.source = windowinterface.textwindow(source)

	def mayclose(self):
		prompt = 'You haven\'t saved your changes yet;\n' + \
			 'do you want to save them before closing?'
		b1 = 'Save'
		b2 = "Don't save"
		b3 = 'Cancel'
		return windowinterface.multchoice(prompt, [b1, b2, b3], -1)

	def setcommands(self, commandlist):
		self.window.set_commandlist(commandlist)

	editors = ['XEDITOR', 'WINEDITOR', 'VISUAL', 'EDITOR']
	def do_edit(self, tmp):
		import os
		for e in self.editors:
			editor = os.environ.get(e)
			if editor:
				break
		else:
			# no editor found
			self.edit_finished_callback()
			return
		stat1 = os.stat(tmp)
		os.system('%s %s' % (editor, tmp))
		stat2 = os.stat(tmp)
		from stat import ST_INO, ST_DEV, ST_MTIME, ST_SIZE
		if stat1[ST_INO] == stat2[ST_INO] and \
		   stat1[ST_DEV] == stat2[ST_DEV] and \
		   stat1[ST_MTIME] == stat2[ST_MTIME] and \
		   stat1[ST_SIZE] == stat2[ST_SIZE]:
			# nothing changed
			self.edit_finished_callback()
			return
		self.edit_finished_callback(tmp)
