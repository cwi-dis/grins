__version__ = "$Id$"

import windowinterface

class TopLevelDialog:
	def show(self):
		if self.window is not None:
			return
		self.window = w = windowinterface.Window(self.basename,
				deleteCallback = (self.close_callback, ()))
		buttons = [('Play', (self.play_callback, ())),
			   # The numbers below correspond with the
			   # positions in the `self.views' list (see
			   # `makeviews' below).
			   ('Player', (self.view_callback, (0,)), 't'),
			   ('Hierarchy view', (self.view_callback, (1,)), 't'),
			   ('Channel view', (self.view_callback, (2,)), 't'),
			   ('Hyperlinks', (self.view_callback, (3,)), 't'),
			   None,
			   ('Save', (self.save_callback, ())),
			   ('Save as...', (self.saveas_callback, ())),
			   ('Restore', (self.restore_callback, ())),
			   ('Close', (self.close_callback, ())),
			   ]
		import Help
		if Help.hashelp():
			buttons.append(None)
			buttons.append(('Help', (self.help_callback, ())))
		if hasattr(self.root, 'source') and \
		   hasattr(windowinterface, 'textwindow'):
			buttons.insert(5, ('View Source...',
					   (self.source_callback, ())))
		self.buttons = self.window.ButtonRow(
			buttons,
			top = None, bottom = None, left = None, right = None,
			vertical = 1)
		self.window.show()

	def hide(self):
		if self.window is None:
			return
		self.window.close()
		self.window = None

	def setbuttonstate(self, i, showing):
		self.buttons.setbutton(i+1, showing)

	def showsource(self, source):
		if self.source is not None and not self.source.is_closed():
			self.source.show()
			return
		self.source = windowinterface.textwindow(self.root.source)

	def mayclose(self):
		prompt = 'You haven\'t saved your changes yet;\n' + \
			 'do you want to save them before closing?'
		b1 = 'Save'
		b2 = "Don't save"
		b3 = 'Cancel'
		return windowinterface.multchoice(prompt, [b1, b2, b3], -1)
