__version__ = "$Id$"

import os, sys, posixpath
import windowinterface
import MMAttrdefs, MMurl
from urlparse import urlparse, urlunparse
from MMExc import *
from Hlinks import *
from AnchorDefs import *
from usercmd import *

from TopLevelDialog import TopLevelDialog

class TopLevel(TopLevelDialog):
	def __init__(self, main, url):
		self.__immediate = 0
		self.__intimer = 0
		self.select_fdlist = []
		self.select_dict = {}
		self._last_timer_id = None
		self.main = main
		utype, host, path, params, query, fragment = urlparse(url)
		dir, base = posixpath.split(path)
		if (not utype or utype == 'file') and \
		   (not host or host == 'localhost'):
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
		url = urlunparse((utype, host, path, params, query, None))
		self.filename = url
		self.source = None
		self.read_it()
		self.makeplayer()
		self.commandlist = [
			CLOSE(callback = (self.close_callback, ())),
			]
		import Help
		if hasattr(Help, 'hashelp') and Help.hashelp():
			self.commandlist.append(
				HELP(callback = (self.help_callback, ())))
		if hasattr(self.root, 'source') and \
		   hasattr(windowinterface, 'textwindow'):
			self.commandlist.append(
				SOURCE(callback = (self.source_callback, ())))

	def __repr__(self):
		return '<TopLevel instance, url=' + `self.filename` + '>'

	def show(self):
		TopLevelDialog.show(self)
		if hasattr(self.root, 'source') and \
		   hasattr(windowinterface, 'textwindow'):
			import settings
			if settings.get('showsource'):
				self.source_callback()

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

	def read_it(self):
##		import time
		import MMmimetypes
		self.changed = 0
##		print 'parsing', self.filename, '...'
##		t0 = time.time()
		mtype = MMmimetypes.guess_type(self.filename)[0]
		if mtype == None and sys.platform == 'mac':
			# On the mac we do something extra: for local files we attempt to
			# get creator and type, and if they are us we assume we're looking
			# at a SMIL file.
			import MacOS
			utype, host, path, params, query, fragment = urlparse(self.filename)
			if (not utype or utype == 'file') and \
			   (not host or host == 'localhost'):
				# local file
				fn = MMurl.url2pathname(path)
				try:
					ct, tp = MacOS.GetCreatorAndType(fn)
				except:
					pass
				else:
					if ct == 'GRIN' and tp == 'TEXT':
						mtype = 'application/x-grins-project'
		if mtype in ('application/x-grins-project', 'application/smil'):
			import SMILTreeRead
			self.root = SMILTreeRead.ReadFile(self.filename, self.printfunc)
		elif mtype == 'application/x-grins-cmif':
			import MMRead
			self.root = MMRead.ReadFile(self.filename)
		else:
			import SMILTreeRead
			if mtype is None or \
			   (mtype[:6] != 'audio/' and
			    mtype[:6] != 'video/'):
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

	def close(self):
		self.destroy()

	def help_callback(self, params=None):
		import Help
		Help.showhelpwindow()

	def setwaiting(self):
		windowinterface.setwaiting()

	def prefschanged(self):
		self.root.ResetPlayability()

	#
	# Global hyperjump interface
	#
	def jumptoexternal(self, anchor, atype, stype=A_SRC_PLAY, dtype=A_DEST_PLAY):
		# XXXX Should check that document isn't active already,
		# XXXX and, if so, should jump that instance of the
		# XXXX document.
		import MMurl
		url, aid = MMurl.splittag(anchor)
		url = MMurl.basejoin(self.filename, url)
		
		# by default, the document target will be handled by GRiNS
		# note: this varib allow to manage correctly the sourcePlaystate attribute
		# as well, even if the target document is not handled by GRiNS
		grinsTarget = 1

		for top in self.main.tops:
			if top is not self and top.is_document(url):
				break
		else:
			try:
				# if the destination document is not a smil/grins document,
				# it's handle by an external application
				import MMmimetypes, MMurl
				utype, url2 = MMurl.splittype(url)
				mtype = MMmimetypes.guess_type(url)[0]
				if mtype in ('application/smil', 'application/x-grins-project', \
					'application/x-grins-cmif'):
					# in this case, the document is handle by grins
					top = TopLevel(self.main, url)
				else:
					grinsTarget = 0
					windowinterface.shell_execute(url)
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

		if grinsTarget:
			top.show()
			node = top.root
			if hasattr(node, 'SMILidmap') and node.SMILidmap.has_key(aid):
				val = node.SMILidmap[aid]
				if type(val) is type(()):
					uid, aid = val
				else:
					uid, aid = val, None
				node = node.context.mapuid(uid)
			if dtype == A_DEST_PLAY:
				top.player.show()
				top.player.playfromanchor(node, aid)
			elif dtype == A_DEST_PAUSE:
				top.player.show()
				top.player.playfromanchor(node, aid)
				top.player.pause(1)
			else:
				print 'jump to external: invalid destination state'
			
		if atype == TYPE_JUMP:
			if grinsTarget:
				self.close()
			else:
				# The hide method doesn't work fine.
				# So, for now stop only the player, instead to hide the window
				self.player.stop()
		elif atype == TYPE_FORK:
			if stype == A_SRC_PLAY:
				pass
			elif stype == A_SRC_PAUSE:
				self.player.pause(1)
			elif stype == A_SRC_STOP:
				self.player.stop()
			else:
				print 'jump to external: invalid source state'
			
		return 1

	def is_document(self, url):
		return self.filename == url

	def _getlocalexternalanchors(self):
		fn = self.filename
		if not '/' in fn:
			fn = './' + fn
		rv = []
		alist = MMAttrdefs.getattr(self.root, 'anchorlist')
		for a in alist:
			rv.append((fn, a[A_ID]))
		return rv

	def getallexternalanchors(self):
		rv = []
		for top in self.main.tops:
			if top is not self:
				rv = rv + top._getlocalexternalanchors()
		return rv
