__version__ = "$Id$"

import windowinterface, WMEVENTS
from usercmd import *
from flags import *

class TopLevelDialog:
	adornments = {
		'toolbar': [
			(ALL, 'Play', PLAY),
			(ALL, 'Player', PLAYERVIEW),
			(ALL, 'Structure View', HIERARCHYVIEW),
			(ALL, 'Timeline View', CHANNELVIEW),
			(ALL, 'Layout View', LAYOUTVIEW),
			(ALL, 'Hyperlinks', LINKVIEW),
			(CMIF, 'User Groups', USERGROUPVIEW),
			(ALL, 'Properties...', PROPERTIES),
			(ALL, 'Source...', SOURCE),
			(ALL, 'Edit Source...', EDITSOURCE),
			(ALL, 'Save', SAVE),
			(ALL, 'Save as...', SAVE_AS),
			(ALL, 'Export...', EXPORT_SMIL),
			(ALL, 'Restore', RESTORE),
			(ALL, 'Close', CLOSE),
			(ALL, 'Help', HELP),
			],
		'toolbarvertical': 1,
		'close': [ CLOSE, ],
		}

	def __init__(self):
		pass

	def show(self):
		if self.window is not None:
			return
		self.adornments['flags'] = curflags()
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

	def showsource(self, source = None, optional=0):
##		print 'opt', optional, self.source, 'text', len(source), 'isclosed', self.source and self.source.is_closed()
		if optional and self.source and not self.source.is_showing():
			self.source = None
			return
		if source is None:
			if self.source is not None:
				if not self.source.is_closed():
					self.source.close()
				self.source = None
			return
		if self.source is not None:
			self.source._children[1].settext(source)
			self.source.show()
			return
		self.source = windowinterface.textwindow(source)

	def mayclose(self):
		prompt = 'Document %s:\n' % self.filename + \
			 "You haven't saved your changes yet;\n" \
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
