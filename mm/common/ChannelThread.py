__version__ = '$Id$'

import mm
from Channel import *
import windowinterface
import GLLock

class _ChannelThread:
	def __init__(self):
		self.threads = None

	def destroy(self):
		del self.threads

	def threadstart(self):
		# This method should be overridden by the superclass.
		# It should be something like
		#	import xxxchannel
		#	return xxxchannel.init()
		raise error, 'threadstart method should be overridden'

	def do_show(self, pchan):
		if debug:
			print 'ChannelThread.do_show('+`self`+')'
		attrdict = {}
		if hasattr(self, 'window'):
			attrdict['rect'] = self.window._rect
			if hasattr(self.window, '_window_id'):
				# GL window interface
				attrdict['wid'] = self.window._window_id
				attrdict['gl_lock'] = GLLock.gl_rawlock
			elif hasattr(self.window, '_form'):
				# Motif windowinterface
				attrdict['widget'] = self.window._form
				attrdict['gc'] = self.window._gc
				attrdict['visual'] = self.window._topwindow._visual
			elif hasattr(self.window, '_hWnd'):
				# Win32 windowinterface
				attrdict['HWND'] = self.window._hWnd
			else:
				print 'can\' work with this windowinterface'
				return 0
		if self._attrdict.has_key('queuesize'):
			attrdict['queuesize'] = self._attrdict['queuesize']
		try:
			self.threads = mm.init(self.threadstart(),
					       self._deviceno, attrdict)
		except ImportError:
			print 'Warning: cannot import mm, so channel ' + \
				  `self._name` + ' remains hidden'
			return 0
		self._player.toplevel.main.setmmcallback(self._deviceno & 0x3f,
			  self._mmcallback)
		return 1

	def do_hide(self):
		if debug:
			print 'ChannelThread.do_hide('+`self`+')'
		if self.threads:
			self.threads.close()
			self.threads = None

	def play(self, node):
		if debug:
			print 'ChannelThread.play('+`self`+','+`node`+')'
		self.play_0(node)
		if not self._is_shown or not node.IsPlayable() \
		   or self.syncplay:
			self.play_1()
			return
		thread_play_called = 0
		if self.threads.armed:
			self.threads.play()
			thread_play_called = 1
		if self._is_shown:
			self.do_play(node)
		self.armdone()
		if not thread_play_called:
			self.playdone(0)

	def playstop(self):
		if debug:
			print 'ChannelThread.playstop('+`self`+')'
		if self._is_shown:
			self.threads.playstop()

	def armstop(self):
		if debug:
			print 'ChannelThread.armstop('+`self`+')'
		if self._is_shown:
			self.threads.armstop()

	def setpaused(self, paused):
		if self._is_shown:
			self.threads.setrate(not paused)

	def stopplay(self, node):
		if self.threads:
			self.threads.finished()

	def callback(self, dummy1, dummy2, event, value):
		if debug:
			print 'ChannelThread.callback'+`self,dummy1,dummy2,event,value`
		if not hasattr(self, '_player'):
			# already destroyed
			return
		if value == mm.playdone:
			if self._playstate == PLAYING:
				self.playdone(0)
			elif self._playstate != PIDLE:
				raise error, 'playdone event when not playing'
		elif value == mm.armdone:
			if self._armstate == ARMING:
				self.arm_1()
			elif self._armstate != AIDLE:
				raise error, 'armdone event when not arming'
		elif value == 3:	# KLUDGE for X movies
			try:
				self.window._gc.SetRegion(self.window._clip)
				self.threads.do_display()
			except AttributeError:
				pass
		else:
			raise error, 'unrecognized event '+`value`

	def _mmcallback(self, val):
		self.callback(0, 0, 0, val)

class ChannelThread(_ChannelThread, Channel):
	def __init__(self, name, attrdict, scheduler, ui):
		Channel.__init__(self, name, attrdict, scheduler, ui)
		_ChannelThread.__init__(self)

	def destroy(self):
		Channel.destroy(self)
		_ChannelThread.destroy(self)

	def playstop(self):
		_ChannelThread.playstop(self)
		Channel.playstop(self)

	def armstop(self):
		_ChannelThread.armstop(self)
		Channel.armstop(self)

	def stopplay(self, node):
		Channel.stopplay(self, node)
		_ChannelThread.stopplay(self, node)

	def setpaused(self, paused):
		Channel.setpaused(self, paused)
		_ChannelThread.setpaused(self, paused)

class ChannelWindowThread(_ChannelThread, ChannelWindow):
	def __init__(self, name, attrdict, scheduler, ui):
		windowinterface.usewindowlock(GLLock.gl_lock)
		ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		_ChannelThread.__init__(self)

	def destroy(self):
		ChannelWindow.destroy(self)
		_ChannelThread.destroy(self)

	def do_show(self, pchan):
		if ChannelWindow.do_show(self, pchan):
			if _ChannelThread.do_show(self, pchan):
				return 1
			ChannelWindow.do_hide(self)
		return 0

	def do_hide(self):
		self.window.setredrawfunc(None)
		_ChannelThread.do_hide(self)
		ChannelWindow.do_hide(self)

	def resize(self, arg, window, event, value):
		# hack for MovieChannel
		self._player.toplevel.setwaiting()
		if hasattr(window, '_gc'):
			window._gc.SetRegion(window._clip)
			window._gc.foreground = window._convert_color(window._bgcolor)
		apply(self.threads.resized, window._rect)
		return

	def playstop(self):
		if GLLock.gl_lock and GLLock.gl_lock.count:
			GLLock.gl_lock.lock.release()
		_ChannelThread.playstop(self)
		if GLLock.gl_lock and GLLock.gl_lock.count:
			GLLock.gl_lock.lock.acquire()
		ChannelWindow.playstop(self)

	def armstop(self):
		if GLLock.gl_lock and GLLock.gl_lock.count:
			GLLock.gl_lock.lock.release()
		_ChannelThread.armstop(self)
		if GLLock.gl_lock and GLLock.gl_lock.count:
			GLLock.gl_lock.lock.acquire()
		ChannelWindow.armstop(self)

	def stopplay(self, node):
		w = self.window
		if w:
			w.setredrawfunc(None)
##		ChannelWindow.stopplay(self, node)
		Channel.stopplay(self, node)   # These 2 lines repl prev.
		self.played_display = None
		if hasattr(w, '_gc'):
			w._gc.SetRegion(w._clip)
			w._gc.foreground = w._convert_color(w._bgcolor)
		_ChannelThread.stopplay(self, node)

	def setpaused(self, paused):
		ChannelWindow.setpaused(self, paused)
		_ChannelThread.setpaused(self, paused)

	def play(self, node):
		if debug:
			print 'ChannelWindowThread.play('+`self`+','+`node`+')'
		self.play_0(node)
		if not self._is_shown or not node.IsPlayable() \
		   or self.syncplay:
			self.play_1()
			return
		self.check_popup()
		if self.armed_display.is_closed():
			# assume that we are going to get a
			# resize event
			pass
#		else:
#			self.armed_display.render()
#		if self.played_display:
#			self.played.display.close()
		self.played_display = self.armed_display
		self.armed_display = None
		thread_play_called = 0
		if self.threads.armed:
			w = self.window
			w.setredrawfunc(self.do_redraw)
			try:
				w._gc.SetRegion(w._clip)
				w._gc.foreground = w._convert_color(self.getbgcolor(node))
			except AttributeError:
				pass
			self.threads.play()
			thread_play_called = 1
		if self._is_shown:
			self.do_play(node)
		self.armdone()
		if not thread_play_called:
			self.playdone(0)

	def do_redraw(self):
		w = self.window
		w._gc.SetRegion(w._clip)
		w._gc.foreground = w._convert_color(w._bgcolor)
		apply(self.threads.resized, w._rect)
