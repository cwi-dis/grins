__version__ = "$Id$"

import os, posixpath
import sys
import windowinterface
import MMAttrdefs, MMurl
from MMExc import *
from EditMgr import EditMgr
import Timing
from ViewDialog import ViewDialog
from Hlinks import TYPE_JUMP, TYPE_CALL, TYPE_FORK

# an empty document
EMPTY = "(seq '1' ((channellist ('root-layout' (type layout) (units 2) (winsize  640 480))) (hyperlinks)))"

from TopLevelDialog import TopLevelDialog

class TopLevel(TopLevelDialog, ViewDialog):
	def __init__(self, main, url, new_file):
		self.waiting = 0
		ViewDialog.__init__(self, 'toplevel_')
		self.select_fdlist = []
		self.select_dict = {}
		self._last_timer_id = None
		self.new_file = new_file
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
		self.main = main
		self.source = None
		self.read_it()
		self.makeviews()
		self.window = None

	def __repr__(self):
		return '<TopLevel instance, url=' + `self.filename` + '>'

	def showstate(self, view, showing):
		for i in range(len(self.views)):
			if view is self.views[i]:
				self.setbuttonstate(i, showing)

	def destroy(self):
		self.editmgr.unregister(self)
		self.editmgr.destroy()
		self.destroyviews()
		self.hide()
		self.root.Destroy()
		import Clipboard
		type, data = Clipboard.getclip()
		if type == 'node' and data is not None:
			Clipboard.setclip('', None)
			data.Destroy()
		for v in self.views:
			v.toplevel = None
		self.views = []
		if self in self.main.tops:
			self.main.tops.remove(self)

	def timer_callback(self):
		self._last_timer_id = None
		self.player.timer_callback()

	def set_timer(self, delay):
		if self._last_timer_id is not None:
			windowinterface.canceltimer(self._last_timer_id)
			self._last_timer_id = None
		if delay:
			self._last_timer_id = windowinterface.settimer(delay,
				  (self.timer_callback, ()))

	#
	# View manipulation.
	#
	def makeviews(self):
		import HierarchyView
		self.hierarchyview = HierarchyView.HierarchyView(self)

		import ChannelView
		self.channelview = ChannelView.ChannelView(self)

		import Player
		self.player = Player.Player(self)

		import LinkEdit
		self.links = LinkEdit.LinkEdit(self)

		# Views that are destroyed by restore (currently all)
		self.views = [self.player, self.hierarchyview,
			      self.channelview, self.links]

	def hideviews(self):
		for v in self.views:
			v.hide()

	def destroyviews(self):
		for v in self.views:
			v.destroy()

	def checkviews(self):
		pass

	#
	# Callbacks.
	#
	def play_callback(self):
		self.setwaiting()
		self.player.show((self.player.playsubtree, (self.root,)))
		self.setready()

	def source_callback(self):
		self.showsource(self.root.source)

	def view_callback(self, viewno):
		self.setwaiting()
		view = self.views[viewno]
		if view.is_showing():
			view.hide()
		else:
			view.show()
		self.setready()

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
			top = TopLevel(self.main, MMurl.pathname2url(filename), 0)
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
		top.setready()

	def open_callback(self):
		cwd = self.dirname
		if cwd:
			cwd = MMurl.url2pathname(cwd)
			if not os.path.isabs(cwd):
				cwd = os.path.join(os.getcwd(), cwd)
		else:
			cwd = os.getcwd()
		windowinterface.FileDialog('Open SMIL file:', cwd, '*.smil',
					   '', self.open_okcallback, None,
					   existing = 1)

	def save_callback(self):
		if self.new_file:
			self.saveas_callback()
			return
		utype, url = MMurl.splittype(self.filename)
		host, url = MMurl.splithost(url)
		if (utype and utype != 'file') or host:
			windowinterface.showmessage('Cannot save to remote URL',
						    mtype = 'warning')
			return
		file = MMurl.url2pathname(url)
		self.setwaiting()
		ok = self.save_to_file(file)
		self.setready()

	def saveas_okcallback(self, filename):
		if not filename:
			return 'no file specified'
		self.setwaiting()
		try:
			if self.save_to_file(filename):
				self.filename = MMurl.pathname2url(filename)
				self.fixtitle()
			else:
				return 1
		finally:
			self.setready()

	def saveas_callback(self):
		cwd = self.dirname
		if cwd:
			cwd = MMurl.url2pathname(cwd)
			if not os.path.isabs(cwd):
				cwd = os.path.join(os.getcwd(), cwd)
		else:
			cwd = os.getcwd()
		windowinterface.FileDialog('Save SMIL file:', cwd, '*.smil',
					   '', self.saveas_okcallback, None)

	def fixtitle(self):
		utype, url = MMurl.splittype(self.filename)
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
		self.window.settitle(self.basename)
		for v in self.views:
			v.fixtitle()

	def save_to_file(self, filename):
		# Get rid of hyperlinks outside the current tree and clipboard
		# (XXX We shouldn't *save* the links to/from the clipboard,
		# but we don't want to throw them away either...)
		roots = [self.root]
		import Clipboard
		type, data = Clipboard.getclip()
		if type == 'node' and data is not None:
			roots.append(data)
		self.context.sanitize_hyperlinks(roots)
		# Get all windows to save their current geometry.
		for v in self.views:
			v.get_geometry()
			v.save_geometry()
		# Make a back-up of the original file...
		try:
			os.rename(filename, make_backup_filename(filename))
		except os.error:
			pass
		print 'saving to', filename, '...'
		try:
			if filename[-4:] == '.smi' or filename[-5:] == '.smil':
				import SMILTreeWrite
				SMILTreeWrite.WriteFile(self.root, filename)
			else:
				import MMWrite
				MMWrite.WriteFile(self.root, filename)
		except IOError, msg:
			windowinterface.showmessage('Save operation failed.\n'+
						    'File: '+filename+'\n'+
						    'Error: '+msg[1])
			return 0
		print 'done saving.'
		self.changed = 0
		self.new_file = 0
		return 1

	def restore_callback(self):
		if self.changed:
			l1 = 'Are you sure you want to re-read the file?\n'
			l2 = '(This will destroy the changes you have made)\n'
			l3 = 'Click OK to restore, Cancel to keep your changes'
			windowinterface.showmessage(
				l1+l2+l3, mtype = 'question',
				callback = (self.do_restore, ()),
				title = 'Destroy?')
			return
		self.do_restore()

	def do_restore(self):
		if not self.editmgr.transaction():
			return
		self.setwaiting()
		self.editmgr.rollback()
		self.editmgr.unregister(self)
		self.editmgr.destroy() # kills subscribed views
		self.context.seteditmgr(None)
		self.root.Destroy()
		self.read_it()
		self.makeviews()
		self.setready()

	def read_it(self):
		self.changed = 0
		if self.new_file:
			if type(self.new_file) == type(''):
				self.do_read_it(self.new_file)
			else:
				import MMRead
				self.root = MMRead.ReadString(EMPTY, self.filename)
		else:
			self.do_read_it(self.filename)
		self.context = self.root.GetContext()
		self.editmgr = EditMgr(self.root)
		self.context.seteditmgr(self.editmgr)
		self.editmgr.register(self)
		
	def do_read_it(self, filename):
## 		import time
		import mimetypes
## 		print 'parsing', filename, '...'
## 		t0 = time.time()
		mtype = mimetypes.guess_type(filename)[0]
		if mtype == 'application/smil':
			import SMILTreeRead
			self.root = SMILTreeRead.ReadFile(filename, self.printfunc)
		elif mtype == 'application/x-cmif':
			import MMRead
			self.root = MMRead.ReadFile(filename)
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
''' % (dur, filename), filename, self.printfunc)
## 		t1 = time.time()
## 		print 'done in', round(t1-t0, 3), 'sec.'


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
		ok = self.close_ok()
		if ok:
			self.destroy()

	def close_ok(self):
		if not self.changed:
			return 1
		reply = self.mayclose()
		if reply == 2:
			return 0
		if reply == 1:
			return 1
		utype, url = MMurl.splittype(self.filename)
		host, url = MMurl.splithost(url)
		if (utype and utype != 'file') or host:
			windowinterface.showmessage('Cannot save to URL',
						    mtype = 'warning')
			return 0
		file = MMurl.url2pathname(url)
		return self.save_to_file(file)

	def help_callback(self, params=None):
		import Help
		Help.showhelpwindow()

	def setwaiting(self):
		if self.waiting: return
		self.waiting = 1
		windowinterface.setcursor('watch')
		for v in self.views:
			v.setwaiting()

	def setready(self):
		if not self.waiting: return
		self.waiting = 0
		for v in self.views:
			v.setready()
		windowinterface.setcursor('')

	#
	# EditMgr interface (as dependent client).
	# This is the first registered client; hence its commit routine
	# will be called first, so it can fix the timing for the others.
	# It also flushes the attribute cache maintained by MMAttrdefs.
	#
	def transaction(self):
		# Always allow transactions
		return 1

	def commit(self):
		# Fix the timing -- views may depend on this.
		self.changed = 1
		MMAttrdefs.flushcache(self.root)
		Timing.changedtimes(self.root)

	def rollback(self):
		# Nothing has happened.
		pass

	def kill(self):
		print 'TopLevel.kill() should not be called!'

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
				top = TopLevel(self.main, url, 0)
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

if os.name == 'posix':
	def make_backup_filename(filename):
		return filename + '~'
else:
	def make_backup_filename(filename):
		return filename + '.BAK'
		
