# Movie channel

# This uses the "VFile" to read and display a "variety" of video formats.

import sys

import os
from stat import *

import MMExc
import MMAttrdefs

import gl
import GL

import VFile


import GLLock

# Errors that VFile operations may raise
VerrorList = VFile.Error, os.error, IOError, RuntimeError, EOFError

from Channel import Channel
from ChannelWindow import ChannelWindow


class MovieWindow(ChannelWindow):
	#
	# Initialization function.
	#
	def init(self, name, attrdict, channel):
		self = ChannelWindow.init(self, name, attrdict, channel)
		self.clear()
		return self
	#
	def __repr__(self):
		return '<MovieWindow instance, name=' + `self.name` + '>'
	#
	def show(self):
		if self.wid <> 0:
			self.setwin()
			return
		ChannelWindow.show(self)
		self.clear()
	#
	def redraw(self):
		if self.wid == 0: return
		gl.reshapeviewport()
		self.erase()
		if self.channel.threads and not self.cleared:
			self.channel.threads.resized()
	#
	def clear(self):
		self.node = self.lookahead = None
		self.cleared = 1
		if self.wid <> 0:
			self.setwin()
			gl.RGBmode()
			gl.gconfig()
			self.rgbmode = 1
			self.erase()
	#
	def erase(self):
		if self.node <> None:
			r, g, b = MMAttrdefs.getattr(self.node, 'bgcolor')
		elif self.attrdict.has_key('bgcolor'):
			r, g, b = self.attrdict['bgcolor']
		else:
			r, g, b = 255, 255, 255
		if not self.cleared:
##			self.vfile.clearto(r, g, b)# XYZZY
##			self.centerimage()
			return
		#
		if self.rgbmode:
			gl.RGBcolor(r, g, b)
		else:
			INDEX = 31 # Overwrite a "harmless" color index
			gl.mapcolor(INDEX, r, g, b)
			gl.color(INDEX)
			gl.gflush()
		#
		gl.clear()
	#
##	def setfile(self, filename, node, do_warm):
##		self.clear()
##		self.vfile = None
##		try:
##			self.vfile = VFile.VinFile().init(filename)
##			if do_warm:
##				try:
##					self.vfile.readcache()
##				except VFile.Error:
##					print filename, ': no cached index'
##		except EOFError:
##			print 'Empty movie file', `filename`
##			return
##		except VerrorList, msg:
##			print 'Cannot open movie file', `filename`, ':', msg
##			return
##		self.node = node
##		self.vfile.magnify = MMAttrdefs.getattr(self.node, 'scale')
##		dummy = self.peekaboo()
##		if self.lookahead <> None and self.is_showing():
##			self.setwin()
##			self.vfile.initcolormap()
##			self.rgbmode = (self.vfile.format == 'rgb')
##			self.centerimage()
	#
	def setfile(self, filename, node, do_warm):
		self.node = self.vfile = self.lookahead = None
		try:
			self.vfile = VFile.RandomVinFile().init(filename)
			if do_warm:
				try:
					self.vfile.readcache()
				except VFile.Error:
					print filename, ': no cached index'
		except EOFError:
			print 'Empty movie file', `filename`
			return
		except VerrorList, msg:
			print 'Cannot open movie file', `filename`, ':', msg
			return
		self.node = node
##		self.vfile.magnify = MMAttrdefs.getattr(self.node, 'scale')
		dummy = self.peekaboo()
		self.rgbmode = (self.vfile.format == 'rgb')
	#
	def popup(self):
		if gl.windepth(self.wid) <> 1:
			self.pop()
			if gl.getdisplaymode() in (0, 5):
				gl.RGBcolor(200, 200, 200) # XXX rather light grey
				gl.clear()
				return
			gl.writemask(0xffffffff)
			gl.clear()
##			if self.vfile:
##				self.vfile.clear()# XYZZY
	#
##	def centerimage(self):
##		w, h = self.vfile.width, self.vfile.height
##		w, h = int(w*self.vfile.magnify), int(h*self.vfile.magnify)
##		W, H = gl.getsize()
##		self.vfile.xorigin, self.vfile.yorigin = (W-w)/2, (H-h)/2
	#
	def peekaboo(self):
		try:
			self.lookahead = self.vfile.getnextframeheader()
			return self.lookahead[0] * 0.001
		except VerrorList:
			self.lookahead = None
			return 0.0
	#
	def done(self):
		return self.lookahead == None
	#
##	def nextframe(self, skip):
##		if self.lookahead == None:
##			return 0.0
##		time, size, chromsize = self.lookahead
##		if self.wid == 0 or skip:
##			try:
##				self.vfile.skipnextframedata(size, chromsize)
##			except VerrorList:
##				return 0.0
##		else:
##			self.setwin()
##			try:
##				data, chromdata = \
##				  self.vfile.getnextframedata(size, chromsize)
##				self.vfile.showframe(data, chromdata)
##			except VerrorList:
##				return 0.0
##		return self.peekaboo()


# XXX Make the movie channel class a derived class from MovieWindow?!

def armdone(arg):
	pass
def stopped(arg):
	pass

class MovieChannel(Channel):
	#
	# Declaration of attributes that are relevant to this channel,
	# respectively to nodes belonging to this channel.
	#
	chan_attrs = ['base_window', 'base_winoff']
	node_attrs = ['file', 'scale', 'bgcolor']
	#
	def init(self, name, attrdict, player):
		self = Channel.init(self, name, attrdict, player)
		self.window = MovieWindow().init(name, attrdict, self)
		self.armed_node = None
		import mm, moviechannel
		self.threads = mm.init(moviechannel.init(), \
			  0, self.deviceno, None)
##		print 'MovieChannel.init: self.threads = ' + `self.threads`
		return self
	#
	def __repr__(self):
		return '<MovieChannel instance, name=' + `self.name` + '>'
	#
	def show(self):
		if self.may_show():
			self.window.show()
	#
	def hide(self):
		self.window.hide()
	#
	def is_showing(self):
		return self.window.is_showing()
	#
	def destroy(self):
##		print 'MovieChannel.destroy'
		if GLLock.gl_lock:
			GLLock.gl_lock.release()
		self.threads.close()
		self.threads = None
		if GLLock.gl_lock:
			GLLock.gl_lock.acquire()
		self.window.destroy()
	#
	def save_geometry(self):
		self.window.save_geometry()
	#
	def do_arm(self, node):
##		print 'MovieChannel.do_arm: self.threads = ' + `self.threads`
		if self.window.vfile:
			import glwindow, mm
			glwindow.devregister(`self.deviceno`+':'+`mm.armdone`,\
				  armdone, 0)
			glwindow.devregister(`self.deviceno`+':'+`mm.stopped`,\
				  stopped, 0)
			if not GLLock.gl_lock:
				GLLock.init()
			self.threads.arm(self.window.vfile.fp, 0, 0, \
				  {'width': self.window.vfile.width, \
				   'height': self.window.vfile.height, \
				   'format': self.window.vfile.format, \
				   'index': self.window.vfile.index, \
				   'c0bits': self.window.vfile.c0bits, \
				   'c1bits': self.window.vfile.c1bits, \
				   'c2bits': self.window.vfile.c2bits, \
				   'offset': self.window.vfile.offset, \
				   'scale': MMAttrdefs.getattr(node, 'scale'), \
				   'wid': self.window.wid, \
				   'bgcolor': MMAttrdefs.getattr(node, 'bgcolor'), \
				   'gl_lock': GLLock.gl_lock}, \
				   None)
		self.armed_node = node
	#
	def arm(self, node):
		if not self.is_showing():
			return
		filename = self.getfilename(node)
		self.window.setfile(filename, node, 1)
		self.do_arm(node)
	#
	def late_arm(self, node):
		filename = self.getfilename(node)
		self.window.setfile(filename, node, 0)
		self.do_arm(node)
	#
	def did_arm(self):
		return (self.armed_node <> None)
	#
	def play(self, node, callback, arg):
		self.node = node
		self.cb = (callback, arg)
		if not self.is_showing():
			import Duration
			duration = Duration.get(node)
			dummy = self.player.enter(duration, 0, \
				self.done, None)
			return
	        if node <> self.armed_node:
			print 'MovieChannel: node not armed'
			self.window.popup() # was: .pop(); --Guido
			self.late_arm(node)
		else:
##			self.window.setfile_2()
			self.window.popup()
		self.armed_node = None
##		self.starttime = self.player.timefunc()
##		self.played = self.skipped = 0
##		self.poll() # Put on the first image right now
##		print 'MovieChannel.play: self.threads = ' + `self.threads`
		import glwindow, mm
		glwindow.devregister(`self.deviceno`+':'+`mm.playdone`, \
			  self.done, None)
		glwindow.devregister(`self.deviceno`+':'+`mm.stopped`, \
			  stopped, 0)
		self.window.cleared = 0
		self.threads.play()
		self.player.arm_ready(self.name)
	#
	#DEBUG: remove dummy entry from queue and call proper done method
	def done(self, arg):
		if not self.node:
			# apparently someone has already called stop()
			return
		Channel.done(self, arg)
		#self.node = None
	#
	def stop(self):
		if GLLock.gl_lock:
			GLLock.gl_lock.release()
		self.threads.stop()
		if GLLock.gl_lock:
			GLLock.gl_lock.acquire()
		Channel.stop(self)
		self.window.vfile = None
	#
	def setrate(self, rate):
		self.threads.setrate(rate)
	#
##	def poll(self):
##		self.qid = None
##		if self.window.done(): # Last frame
##			if self.played:
##				print 'Played ', self.played*100/ \
##					  (self.played+self.skipped), \
##					  '% of the frames'
##			self.done(None)
##			return
##		else:
##			t = self.window.nextframe(0)
##			self.played = self.played + 1
##			now = self.player.timefunc()
##			while t and self.starttime + t <= now:
##				t = self.window.nextframe(1)
##				self.skipped = self.skipped + 1
##			self.qid = self.player.enterabs(self.starttime + t, \
##				1, self.poll, ())
	#
	def reset(self):
		self.window.clear()
		self.node = None # Attempt to fix obscure bug --Guido
	#
	def clear(self):
		print 'MOVIECHANNEL CLEAR!'
		self.reset()
	#
	def getduration(self, node):
		import MovieDuration
		filename = self.getfilename(node)
		try:
			return MovieDuration.get(filename)
		except IOError:
			print 'cannot open movie file to get duration:',
			print `filename`
			return MMAttrdefs.getattr(node, 'duration')
	#
	def setwaiting(self):
		self.window.setwaiting()
	#
	def setready(self):
		self.window.setready()
	#
