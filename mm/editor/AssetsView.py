__version__ = "$Id$"

from AssetsViewDialog import AssetsViewDialog
from usercmd import *
import MMNode
from MMTypes import *
import MMAttrdefs
import urlparse
import posixpath
import string
import usercmd

class AssetsView(AssetsViewDialog):
	COLUMNLIST={
		'all':[
			('left', 120, 'Name'),
			('left', 70, 'Type'),
			('right', 50, 'Used'),
			('left', 200, 'URL'),
		],
		'unused':[
			('left', 120, 'Name'),
			('left', 70, 'Type'),
			('left', 200, 'URL'),
		],
		'clipboard':[
			('left', 120, 'Name'),
			('left', 70, 'Type'),
		],
	}

	def __init__(self, toplevel):
		self.toplevel = toplevel
		self.root = toplevel.root
		self.context = self.root.context
		self.editmgr = self.context.editmgr
		self.whichview = 'unused'
		AssetsViewDialog.__init__(self)

	def fixtitle(self):
		pass
	def get_geometry(self):
		pass
	def save_geometry(self):
		pass

	def destroy(self):
		self.hide()
		AssetsViewDialog.destroy(self)

	def show(self):
		if self.is_showing():
			AssetsViewDialog.show(self)
			return
		AssetsViewDialog.show(self)
		self.editmgr.register(self, want_clipboard=1)
		self.setview(self.whichview)

	def hide(self):
		if not self.is_showing():
			return
		self.editmgr.unregister(self)
		AssetsViewDialog.hide(self)

	def transaction(self,type):
		return 1		# It's always OK to start a transaction

	def rollback(self):
		pass

	def commit(self, type=None):
		# This isn't really needed always, but who cares.
		self.setview(self.whichview)

	def clipboardchanged(self):
		self.setview(self.whichview)

	def kill(self):
		self.destroy()

	def setview(self, which):
		self.whichview = which
		self.setviewbutton(which)
		self.setlistheaders(self.COLUMNLIST[which])
		if which == 'all':
			self.listdata = self.getallassets()
			cmdlist = []
		elif which == 'unused':
			self.listdata = self.getunusedassets()
			cmdlist = [
				usercmd.CUT(callback=(self.callback_cut, ())),
				usercmd.COPY(callback=(self.callback_copy, ())),
				usercmd.PASTE(callback=(self.callback_paste, ())),
				usercmd.DELETE(callback=(self.callback_delete, ())),
			]
		else:
			self.listdata = self.getclipboard()
			cmdlist = []
		# XXX Sort
		# Remove first field
		listdata = map(lambda x:x[1:], self.listdata)
		self.setlistdata(listdata)
		self.setcommandlist(cmdlist)

	def callback_cut(self):
		i = self.getselection()
		if i < 0:
			print "No selection"
			return
		item = self.listdata[i][0]
		if not self.editmgr.transaction():
			print "No transaction"
			return
		self.editmgr.delasset(item)
		self.editmgr.commit()
		self.__clean_clipboard()
		self.editmgr.setclip('node', item)

	def callback_paste(self):
		tp, data = self.editmgr.getclip()
		if not tp in ('node', 'multinode'):
			print 'cannot paste', (tp, data)
			return
		if tp == 'node':
			tp = 'multinode'
			data = [data]
		if not self.editmgr.transaction():
			print 'No transaction'
			return
		for node in data:
			self.editmgr.addasset(node)
		self.editmgr.commit()

	def callback_copy(self):
		i = self.getselection()
		if i < 0:
			print "No selection"
			return
		item = self.listdata[i][0]
		self.__clean_clipboard()
		self.editmgr.setclip('node', item)

	def callback_delete(self):
		i = self.getselection()
		if i < 0:
			print "No selection"
			return
		item = self.listdata[i][0]
		if not self.editmgr.transaction():
			print "No transaction"
			return
		self.editmgr.delasset(item)
		self.editmgr.commit()
		# XXX item.Destroy() ???

	def __clean_clipboard(self):
		# Note: after this call you *MUST* set the clipboard to
		# a new value
		t,n = self.editmgr.getclip()
		if t == 'node' and n is not None:
			n.Destroy()
		elif t == 'multinode' and n is not None:
			for i in n:
				i.Destroy()

	def getunusedassets(self):
		assetlist = []
		for node in self.context.getassets():
			# XXX Logic is suboptimal: we consider all ext
			# nodes without ids and with URLs as pure media items,
			# all others as clippings.
			tp = node.GetType()
			if tp == 'ext':
				url = node.GetRawAttr('file')
			else:
				url = ''
			name = MMAttrdefs.getattr(node, 'name')
			if tp == 'ext' and url and not name:
				mimetype = node.GetComputedMimeType()
				mimetype = string.split(mimetype, '/')[0]
				pathname = urlparse.urlparse(url)[2]
				shortname = posixpath.split(pathname)[1]
				assetlist.append((mimetype, mimetype, shortname, url))
			else:
				assetlist.append((node, tp, name, tp, ''))
		return assetlist

	def getallassets(self):
		assetdict = {}
		# First add the unused assets
		for node in self.context.getassets():
			if node.getClassName() == 'MMNode':
				self._getallassetstree(node, assetdict, intree=0)
		# and now add the used assets
		self._getallassetstree(self.root, assetdict)
		assetlist = []
		# For now we ignore the nodes
		for url, v in assetdict.items():
			mimetype, nodelist = v
			pathname = urlparse.urlparse(url)[2]
			shortname = posixpath.split(pathname)[1]
			assetlist.append((None, mimetype, shortname, mimetype, `len(nodelist)`, url))
		return assetlist

	def _getallassetstree(self, node, dict, intree=1):
		rv = []
		tp = node.GetType()
		if tp == 'ext':
			url = node.GetRawAttr('file')
			if url:
				mimetype = node.GetComputedMimeType()
				mimetype = string.split(mimetype, '/')[0]
				if intree:
					if dict.has_key(url):
						mimetype, nodelist = dict[url]
						nodelist.append(node)
					else:
						dict[url] = mimetype, [node]
				else:
					# Not in tree, so we're picking up from the
					# unused assests list. Don't store the nodes.
					if not dict.has_key(url):
						dict[url] = mimetype, []
		if tp in interiortypes:
			for ch in node.GetChildren():
				self._getallassetstree(ch, dict)

	def getclipboard(self):
		tp, data = self.editmgr.getclip()
		if tp == 'node':
			data = [data]
		if tp == 'node' or tp == 'multinode':
			rv = []
			for n in data:
				ntype = n.GetType()
				name = MMAttrdefs.getattr(n, 'name')
				rv.append((None, ntype, name, ntype))
			return rv
		name = ''
		if tp in ('viewport', 'region'):
			name = data.name
		return [(None, tp, name, tp)]

	# Callbacks from the UI
	def setview_callback(self, which):
		print 'setview', which
		self.setview(which)

	def select_callback(self, number):
		print 'select', number

	def sort_callback(self, column):
		print 'sort', column