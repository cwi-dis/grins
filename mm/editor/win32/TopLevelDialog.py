__version__ = "$Id$"

import windowinterface, WMEVENTS
from usercmd import *
from wndusercmd import *


""" @win32doc|TopLevelDialog
There is one to one corespondance between a TopLevelDialog
instance and a document, and a TopLevelDialog
instance with an MDIFrameWnd. The document level commands
are enabled. This class has acces to the document and
can display its various views and its source
"""

import bitrates, languages

class TopLevelDialog:
	def __init__(self):
		self.commandlist = self.commandlist + [
			PAUSE(callback = (self.pause_callback, ())),
			STOP(callback = (self.stop_callback, ())),
			TB_PLAY(callback = (self.play_callback, ())),
			TB_PAUSE(callback = (self.pause_callback, ())),
			TB_STOP(callback = (self.stop_callback, ())),
			SCHEDDUMP(callback = (self.__dump, ())),
		]

	def __dump(self):
		self.player.scheduler.dump()

	def show(self):
		if self.window is not None:
			return
		import settings, bitrates, languages
		bitrate = settings.get('system_bitrate')
		rates = []
		initbitrate = bitrates.bitrates[0][1]
		for val, str in bitrates.bitrates:
			rates.append(str)
			if val <= bitrate:
				initbitrate = str
		language = settings.get('system_language')
		langs = []
		initlang = 'English'	# we know this occurs
		for val, str in languages.languages:
			langs.append(str)
			if language == val:
				initlang = str

		adornments = {
			'pulldown': [(rates, self.bitratecb, initbitrate),
				     (langs, self.languagecb, initlang),
				     ],
			}

		self.window = windowinterface.newdocument(self, 
			adornments = adornments,commandlist = self.commandlist)
		import Player
		self.setplayerstate(Player.STOPPED)

	def hide(self):
		if self.window is None:
			return
		self.window.close()
		self.window = None

	def setbuttonstate(self, command, showing):
		self.window.set_toggle(command, showing)

	def setplayerstate(self, state):
		self.window.setplayerstate(state)

	def showsource(self, source = None, optional=0, readonly = 0):
		if source is None:
			if self.source is not None:
				self.source.close()
				self.source = None
		else:
			if self.source is not None:
				self.source.settext(source)
			else:
				self.source = self.window.textwindow(source, readonly=1)
				self.source.setmother(self)

	def mayclose(self):
		prompt = 'You haven\'t saved your changes yet;\n' + \
			 'do you want to save them before closing?'
		return windowinterface.GetYesNoCancel(prompt,self.window)

	# doesn't seem to work
	# kk: you must pass a context string as a second arg
	def setcommands(self, commandlist):
		self.window.set_commandlist(commandlist,'document')

	def do_edit(self, tmp):
		import os

		# use only notepad for now
		editor='Notepad'
		stat1 = os.stat(tmp)
		import win32api,win32con
		try:
			win32api.WinExec('%s %s' % (editor, tmp),win32con.SW_SHOW)
		except:	
			# no editor found
			self.edit_finished_callback()

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
