from debug import debug
from Channel import Channel
import string
import sys
import VCR
import dialogs
import VcrIndex
import MMAttrdefs

[V_NONE, V_SPR, V_SB, V_READY, V_PLAYING, V_ERROR] = range(6)

class VcrChannel(Channel):
	def init(self, name, attrdict, scheduler, ui):
		self = Channel.init(self, name, attrdict, scheduler, ui)
		self.vcr = VCR.VCR().init()
		self.vcr.setcallback(self.vcr_ready, None)
		toplevel = self._player.toplevel
		toplevel.select_setcallback(self.vcr, self.vcr.poll, ())
		self.vcrstate = V_NONE
		return self

	def __repr__(self):
		return '<VcrChannel instance, name=' + `self._name` + '>'

	def vcr_ready(self, dummy):
		if self.vcrstate == V_SPR:
			d = self.vcr.edit_pb_standby()
			self.vcrstate = V_SB
		elif self.vcrstate == V_SB:
			self.vcrstate = V_READY
			self.arm_1()
			dummy = self.vcr.mute('audio', 0)
			dummy = self.vcr.mute('video', 0)
			# XXXX Send ARM_DONE event.
		elif self.vcrstate == V_PLAYING:
			self.armdone()
			self.playdone(None)
			dummy = self.vcr.stop()
			self.vcrstate = V_NONE
		else:
			raise 'vcr_ready callback with state==', self.vcrstate
			
	def do_arm(self, node):	# Override default method
		if self.vcrstate <> V_NONE:
			raise 'do_arm with vcrstate<>V_NONE'
		while 1:
			try:
				self.vcr.initvcr(5)
				break
			except VCR.error, arg:
				pass   # Fall thru
			i = dialogs.multchoice('VCR not ready:\n' + arg, \
				  ['Hide channel', 'try again'], 0)
			if i == 0:
				self.hide()
				return 0
		dummy = self.vcr.fmmode('dnr')
		summy = self.vcr.mute('audio', 1)
		dummy = self.vcr.mute('video', 1)
		ntype = node.GetType()
		start = None
		stop = None
		if ntype == 'imm':
			list = node.GetValues()
			#
			# This code is not very elegant. It expects python-
			# format tupels (h,m,s,f) for start/stop time.
			#
			if len(list) in (1,2):
				try:
					start = eval(list[0])
					if type(start) <> type(()) or \
						  len(start) <> 4:
						raise 'foo'
				except 'DBGDBG':
					start = None
			if len(list) == 2:
				try:
					stop = eval(list[1])
					if type(stop) <> type(()) or \
						  len(start) <> 4:
						raise 'foo'
				except:
					stop = None
		elif ntype == 'ext':
			start, stop = self.getstartstopindex(node)

		if not start:
			start = (0,0,5,0)    # Pretty arbitrary
		start = self.vcr.tc2addr(start)
		start = start + 3*25 - 5     # Preroll point
		start = self.vcr.addr2tc(start)
		d = self.vcr.inentry(start)
		if stop:
			d = self.vcr.outentry(stop)
		else:
			d = self.vcr.outentry('reset')
		if not self.vcr.search_preroll():
			print 'Video error'
			self.vcrstate = V_ERROR
			return 1
		self.vcrstate = V_SPR
		return 0

	def play(self, node):	# XXX Override Channel method.
		self.play_0(node)
		if self.vcrstate == V_ERROR or not self.is_showing():
			self.play_1()
			return
		if self.vcrstate <> V_READY:
			raise 'do_play with state<>V_READY'
		d = self.vcr.edit_play()
		self.vcrstate = V_PLAYING

	def playstop(self):
		if debug:
			print 'VcrChannel.playstop('+`self`+')'
		d = self.vcr.initvcr()
		d = self.vcr.stop()
		self.vcrstate = V_NONE
		Channel.playstop(self)

	def armstop(self):
		if debug:
			print 'VcrChannel.armstop('+`self`+')'
		d = self.vcr.initvcr()
		d = self.vcr.stop()
		self.vcrstate = V_NONE
		Channel.armstop(self)

	def getstartstopindex(self, node):
		name = MMAttrdefs.getattr(node, 'file')
		endscene = None
		try:
			nms = string.splitfields(name, ':')
			if len(nms) == 2:
				[name, movie] = nms
				scene = '-ALL-'
				endscene = '-END-'
			elif len(nms) == 3:
				[name, movie, scene] = nms
			else:
				[name, movie, scene, endscene] = nms
		except:
			print 'vcrchannel: ill-formatted filename:', nms
			return None, None
		index = VcrIndex.VcrIndex().init(name)
		try:
			index.movie_select(movie)
		except VcrIndex.error:
			print 'vcrchannel: no movie named', movie
			return None, None
		try:
			index.scene_select(scene)
		except VcrIndex.error:
			print 'vcrchannel: no such scene', scene
			return None, None
		start = index.pos_get()
		if not endscene:
			names = index.get_scenenames()
			i = names.index(scene) + 1
			if i < len(names):
				endscene = names[i]
		if endscene:
			index.scene_select(endscene)
			stop = index.pos_get()
		else:
			stop = None
		return start, stop
		
