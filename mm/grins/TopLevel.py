__version__ = "$Id$"

import os, sys, posixpath
import windowinterface
import MMAttrdefs, MMurl
from MMExc import *
import Timing
from Hlinks import TYPE_JUMP, TYPE_CALL, TYPE_FORK
from usercmd import *

# an empty document
EMPTY = "(seq '1' ((channellist) (hyperlinks)))"

from TopLevelDialog import TopLevelDialog

class TopLevel(TopLevelDialog):
	def __init__(self, main, url):
		self.__immediate = 0
		self.__intimer = 0
		self.waiting = 0
		self.select_fdlist = []
		self.select_dict = {}
		self._last_timer_id = None
		self.main = main
		utype, url = MMurl.splittype(url)
		host, url = MMurl.splithost(url)
		dir, base = posixpath.split(url)
		if not utype and not host:
			# local file
			self.dirname = dir
		else:
			# remote file
			self.dirname = ''
		if base[-5:] == '.cmif':
			self.basename = base[:-5]
		elif base[-4:] == '.smi':
			self.basename = base[:-4]
		elif base[-5:] == '.smil':
			self.basename = base[:-5]
		else:
			self.basename = base
		if host:
			url = '//%s%s' % (host, url)
		if utype:
			url = '%s:%s' % (utype, url)
		self.filename = url
		self.source = None
		self.read_it()
		self.makeplayer()
		self.commandlist = [
			CLOSE(callback = (self.close_callback, ())),
			]
		import Help
		if Help.hashelp():
			self.commandlist.append(
				HELP(callback = (self.help_callback, ())))
		if hasattr(self.root, 'source') and \
		   hasattr(windowinterface, 'textwindow'):
			self.commandlist.append(
				SOURCE(callback = (self.source_callback, ())))

	def __repr__(self):
		return '<TopLevel instance, url=' + `self.filename` + '>'

	def destroy(self):
		if self in self.main.tops:
			self.main.tops.remove(self)
		self.destroyplayer()
		self.hide()
		self.root.Destroy()

	def timer_callback(self):
		self.__intimer = 1
		self.setwaiting()
		self._last_timer_id = None
		self.player.timer_callback()
		while self.__immediate:
			self.__immediate = 0
			self.player.timer_callback()
		self.setready()
		self.__intimer = 0

	def set_timer(self, delay):
		if self._last_timer_id is not None:
			windowinterface.canceltimer(self._last_timer_id)
			self._last_timer_id = None
		self.__immediate = 0
		if delay:
			if delay <= 0.01 and self.__intimer:
				self.__immediate = 1
			else:
				self._last_timer_id = windowinterface.settimer(
					delay, (self.timer_callback, ()))

	#
	# View manipulation.
	#
	def makeplayer(self):
		import Player
		self.player = Player.Player(self)

	def destroyplayer(self):
		self.player.destroy()
		self.player = None

	#
	# Callbacks.
	#
	def source_callback(self):
		self.showsource(self.root.source)

	def open_okcallback(self, filename):
		if os.path.isabs(filename):
			cwd = os.getcwd()
			if os.path.isdir(filename):
				dir, file = filename, os.curdir
			else:
				dir, file = os.path.split(filename)
			# XXXX maybe should check that dir gets shorter!
			while len(dir) > len(cwd):
				dir, f = os.path.split(dir)
				file = os.path.join(f, file)
			if dir == cwd:
				filename = file
		try:
			top = TopLevel(self.main, MMurl.pathname2url(filename))
		except:
			msg = sys.exc_value
			if type(msg) is type(self):
				if hasattr(msg, 'strerror'):
					msg = msg.strerror
				else:
					msg = msg.args[0]
			windowinterface.showmessage('Open operation failed.\n'+
						    'File: '+filename+'\n'+
						    'Error: '+`msg`)
			return
		top.show()
		top.player.show()
		top.player.playsubtree(top.root)
		top.setready()

	def read_it(self):
## 		import time
		import mimetypes
		self.changed = 0
##		print 'parsing', self.filename, '...'
##		t0 = time.time()
		mtype = mimetypes.guess_type(self.filename)[0]
		if mtype == 'application/smil':
			import SMILTreeRead
			self.root = SMILTreeRead.ReadFile(self.filename, self.printfunc)
		elif mtype == 'application/x-cmif':
			import MMRead
			self.root = MMRead.ReadFile(self.filename)
		else:
			import SMILTreeRead
			if mtype[:6] != 'audio/' and \
			   mtype[:6] != 'video/':
				dur = ' dur="indefinite"'
			else:
				dur = ''
			self.root = SMILTreeRead.ReadString('''\
<smil>
  <body>
    <ref%s src="%s"/>
  </body>
</smil>
''' % (dur, self.filename), self.filename, self.printfunc)
##		t1 = time.time()
##		print 'done in', round(t1-t0, 3), 'sec.'
		self.context = self.root.GetContext()

	def printfunc(self, msg):
		windowinterface.showmessage('while reading %s\n\n' % self.filename + msg)

	def close_callback(self):
		self.setwaiting()
		if self.source and not self.source.is_closed():
			self.source.close()
		self.source = None
		self.close()
		self.setready()

	def close(self):
		self.destroy()

	def help_callback(self, params=None):
		import Help
		Help.showhelpwindow()

	def setwaiting(self):
		if self.waiting: return
		self.waiting = 1
		windowinterface.setcursor('watch')
		self.player.setwaiting()

	def setready(self):
		if not self.waiting: return
		self.waiting = 0
		if self.player is not None:
			self.player.setready()
		windowinterface.setcursor('')

	#
	# Global hyperjump interface
	#
	def jumptoexternal(self, uid, aid, atype):
		# XXXX Should check that document isn't active already,
		# XXXX and, if so, should jump that instance of the
		# XXXX document.
		import MMurl
		if '/' not in uid:
			url = self.filename
		elif uid[-2:] == '/1':
			url = uid[:-2]
		else:
			url = uid
		url = MMurl.basejoin(self.filename, url)
		for top in self.main.tops:
			if top is not self and top.is_document(url):
				break
		else:
			try:
				top = TopLevel(self.main, url)
			except:
				msg = sys.exc_value
				if type(msg) is type(self):
					if hasattr(msg, 'strerror'):
						msg = msg.strerror
					else:
						msg = msg.args[0]
				windowinterface.showmessage(
					'Open operation failed.\n'+
					'File: '+url+'\n'+
					'Error: '+`msg`)
				return 0
		top.show()
		node = top.root
		if '/' not in uid:
			try:
				node = top.root.context.mapuid(uid)
			except NoSuchUIDError:
				print 'uid not found in document'
		top.player.show((top.player.playfromanchor, (node, aid)))
		if atype == TYPE_CALL:
			self.player.pause(1)
		elif atype == TYPE_JUMP:
			self.close()
		return 1

	def is_document(self, url):
		return self.filename == url

	def _getlocalexternalanchors(self):
		fn = self.filename
		if not '/' in fn:
			fn = './' + fn
		rv = []
		alist = MMAttrdefs.getattr(self.root, 'anchorlist')
		for i, t, v in alist:
			rv.append((fn, i))
		return rv

	def getallexternalanchors(self):
		rv = []
		for top in self.main.tops:
			if top is not self:
				rv = rv + top._getlocalexternalanchors()
		return rv
