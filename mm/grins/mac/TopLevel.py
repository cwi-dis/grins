__version__ = "$Id$"

import windowinterface, WMEVENTS
import Timing
from MMExc import MSyntaxError

class TopLevel:
	def __init__(self, main, filename):
		import MMTree, Player, MMurl
		# convert filename to URL
		utype, url = MMurl.splittype(filename)
		if not utype or utype not in ('http', 'file', 'ftp', 'rtsp'):
			# assume filename using local convention
			url = MMurl.pathname2url(filename)
			utype, url = MMurl.splittype(url)
		if utype:
			url = '%s:%s' % (utype, url)
		self.filename = url
		print 'URL=', self.filename
		self.main = main
		self.waiting = 0
		self.read_it()
		self.player = Player.Player(self)
		self._last_timer_id = None

	def __repr__(self):
		return '<TopLevel instance, filename=' + `self.filename` + '>'

	def close(self):
		import windowinterface
		self.hide()
		windowinterface.close()

	def show(self, aftershow = None):
		import windowinterface, GLLock
		windowinterface.usewindowlock(GLLock.gl_lock)
		self.player.show(aftershow)

	def hide(self):
		self.player.hide()


	def read_it(self):
		import time
		import mimetypes
		
		# Add our default smil and cmif types, if needed
		if not mimetypes.types_map.has_key('.smil'):
			mimetypes.types_map['.smil'] = 'application/smil'
		if not mimetypes.types_map.has_key('.smi'):
			mimetypes.types_map['.smi'] = 'application/smil'
		if not mimetypes.types_map.has_key('.cmif'):
			mimetypes.types_map['.cmif'] = 'application/cmif'
			
		self.changed = 0
		print 'parsing', self.filename, '...'
		t0 = time.time()
		mtype = mimetypes.guess_type(self.filename)[0]
		if mtype is None or mtype == 'text/html':
			import SMILTree
			self.root = SMILTree.ReadString('''\
<smil>
  <head>
    <layout>
      <channel id="html"/>
    </layout>
  </head>
  <body>
    <text src="%s" channel="html"/>
  </body>
</smil>
''' % self.filename, self.filename)
		elif mtype == 'application/smil':
			import SMILTree
			self.root = SMILTree.ReadFile(self.filename)
		elif mtype == 'application/x-cmif':
			import MMTree
			self.root = MMTree.ReadFile(self.filename)
		else:
			raise MSyntaxError, 'unknown file type'
		t1 = time.time()
		print 'done in', round(t1-t0, 3), 'sec.'
		Timing.changedtimes(self.root)
		self.context = self.root.GetContext()

	def play(self):
		self.setwaiting()
		if self.player.playing:
			self.player.stop()
		self.player.playsubtree(self.root)
		self.setready()

	def stop(self):
		self.setwaiting()
		self.player.stop()
		self.setready()

	def pause(self):
		self.player.togglepause()

	def setwaiting(self):
		if self.waiting: return
		self.waiting = 1
		import windowinterface
		windowinterface.setcursor('watch')
		self.player.setwaiting()

	def setready(self):
		if not self.waiting: return
		self.waiting = 0
		self.player.setready()
		import windowinterface
		windowinterface.setcursor('')

	def set_timer(self, delay):
		if self._last_timer_id:
			windowinterface.canceltimer(self._last_timer_id)
			self._last_timer_id = None
		if delay:
			self._last_timer_id = windowinterface.settimer(delay,
				  (self.timer_callback, ()))

	def timer_callback(self):
		self._last_timer_id = None
		self.player.timer_callback()

	def keyboard_callback(self, dummy, window, event, value):
		if value == 'p':
			self.pause()
		elif value == 'P':
			self.play()
		elif value == 'S':
			self.stop()
		elif value == 'Q':
			self.main.do_exit()
		elif value == 'd':
			self.player.dumpbaglist()
		elif value == 'D':
			self.player.scheduler.dump()

	#
	# Global hyperjump interface
	#
	def jumptoexternal(self, uid, aid, type):
		# XXXX Should check that document isn't active already,
		# XXXX and, if so, should jump that instance of the
		# XXXX document.
		main = self.main
		import MMurl
		if '/' not in uid:
			filename = self.filename
		elif uid[-2:] == '/1':
			filename = uid[:-2]
		else:
			filename = uid
		try:
			filename = MMurl.urlretrieve(filename)[0]
		except IOError, msg:
			windowinterface.showmessage(
				'Open operation failed.\n'+
				'File: '+filename+'\n'+
				'Error: '+msg[1])
			return 0
		for top in main.tops:
			if top is not self and top.is_document(filename):
				break
		else:
			import MMExc
			try:
				top = TopLevel(main, filename)
			except (IOError, MMExc.MTypeError, MMExc.MSyntaxError), msg:
				windowinterface.showmessage(
					'Open operation failed.\n'+
					'File: '+filename+'\n'+
					'Error: '+`msg`)
				return 0
			main.tops.append(top)
		top.show()
		node = top.root
		if '/' not in uid:
			try:
				node = top.root.context.mapuid(uid)
			except NoSuchUIDError:
				print 'uid not found in document'
		top.player.show((top.player.playfromanchor, (node, aid)))
		if type == TYPE_CALL:
			self.pause()
		elif type == TYPE_JUMP:
			self.close()
		return 1
	#
	def is_document(self, filename):
		import posix

		try:
			ourdata = posix.stat(self.filename)
			hisdata = posix.stat(filename)
		except posix.error:
			return 0
		return (ourdata == hisdata)
