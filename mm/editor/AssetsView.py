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
			('left', 50, 'Type'),
			('left', 100, 'Name'),
			('right', 50, 'Used'),
			('left', 200, 'URL'),
		],
		'unused':[
			('left', 50, 'Type'),
			('left', 100, 'Name'),
			('left', 200, 'URL'),
		],
		'clipboard':[
			('left', 50, 'Type'),
			('left', 100, 'Name'),
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
##		self.commit()
		AssetsViewDialog.show(self)
##		self.editmgr.register(self)
		self.setview(self.whichview)

	def hide(self):
		if not self.is_showing():
			return
##		self.editmgr.unregister(self)
		AssetsViewDialog.hide(self)

	def transaction(self,type):
		return 1		# It's always OK to start a transaction

	def rollback(self):
		pass

##	def commit(self, type=None):
##		transitions = self.context.transitions
##		trnames = transitions.keys()
##		trnames.sort()
##		selection = self.getgroup()
##		if selection is not None:
##			if transitions.has_key(selection):
##				selection = trnames.index(selection)
##			else:
##				selection = None
##		self.setgroups(trnames, selection)

	def kill(self):
		self.destroy()

	def setview(self, which):
		self.whichview = which
		self.setviewbutton(which)
		self.setlistheaders(self.COLUMNLIST[which])
		if which == 'all':
			self.setlistdata(self.getallassets())
		elif which == 'unused':
			self.setlistdata(self.getunusedassets())
		else:
			self.setlistdata(self.getclipboard())
		if which == 'unused':
			cmdlist = [
				usercmd.CUT(callback=(self.callback_cut, ())),
				usercmd.COPY(callback=(self.callback_copy, ())),
				usercmd.PASTE(callback=(self.callback_paste, ())),
				usercmd.DELETE(callback=(self.callback_delete, ())),
			]
		else:
			cmdlist = []
		self.setcommandlist(cmdlist)

	def callback_cut(self):
		print "cut"

	def callback_paste(self):
		print "paste"

	def callback_copy(self):
		print "copy"

	def callback_delete(self):
		print "delete"

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
				assetlist.append((tp, tp, name, ''))
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
			assetlist.append((mimetype, mimetype, shortname, `len(nodelist)`, url))
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
				rv.append((ntype, ntype, name))
			return rv
		return [(tp, tp, '')]

	# Callbacks from the UI
	def setview_callback(self, which):
		print 'setview', which
		self.setview(which)

	def select_callback(self, number):
		print 'select', number

	def sort_callback(self, column):
		print 'sort', column