__version__ = "$Id$"

#
# WIN32 HTML channel.
#

""" @win32doc|HtmlChannel
The HtmlChannel extends the ChannelWindow

For this channel to work the window
must support beyond the standard interface
the following interface:

interface IHtmlWnd:
	def RetrieveUrl(self,url):pass
	def DestroyHtmlCtrl(self):pass
	def setanchorcallback(self,cbanchor):pass

The window or an agent of the window is supposed
to call back the HtmlChannel's callback set by
the setanchorcallback method when a cmif: anchor
is fired.

The _SubWindow defined in lib/win32/_CmifView.py
supports this interface

Note:
For not local files we get the url by calling
the channel's method getfileurl(node) and pass
it directly through RetrieveUrl.
For local files we follow the Internet Explorer
convention of passing the absolute local filename
through RetrieveUrl.
"""
import Channel

# node attributes
import MMAttrdefs

# url parsing
import os, ntpath, urllib, MMurl

from AnchorDefs import *
import sys, string
#import WMEVENTS

import windowinterface

error = 'HtmlChannel.error'

# channel types
[SINGLE, HTM, TEXT, MPEG] = range(4)

class HtmlChannel(Channel.ChannelWindow):
	node_attrs = Channel.ChannelWindow.node_attrs + ['fgcolor', 'font']
	_window_type = HTM

	def __init__(self, name, attrdict, scheduler, ui):
		self.played_str = ()
		self.__errors=[]
		self._tempmap={}
		
		# release any resources on exit
		windowinterface.addclosecallback(self.release_res,())
		
		Channel.ChannelWindow.__init__(self, name, attrdict, scheduler, ui)

	def __repr__(self):
		return '<HtmlChannel instance, name=' + `self._name` + '>'
	
	def do_hide(self):
		if self.window and hasattr(self.window,'DestroyHtmlCtrl'):
			self.window.DestroyHtmlCtrl()
		Channel.ChannelWindow.do_hide(self)

	def destroy(self):
		if self.window and hasattr(self.window,'DestroyHtmlCtrl'):
			self.window.DestroyHtmlCtrl()
			self.window.setredrawfunc(None)
		self.cleartemp()
		Channel.ChannelWindow.destroy(self)

	def release_res(self):
		if self.window and hasattr(self.window,'DestroyHtmlCtrl'):
			self.window.DestroyHtmlCtrl()

	def do_arm(self, node, same=0):
		if not same:
			try:
				self.armed_str = self.getstring(node)
			except:
				self.armed_str = 'Cannot Open: '+self.getfileurl(node)
				self.__errors.append(node)
		return 1

	def do_play(self, node):
		if node.type == 'ext':
			url=self.getfileurl(node)
			url=self.toabs(url)
		else: 
			url=self.totemp(node,self.armed_str)

		if node in self.__errors:
			url='about:'+ self.armed_str

		# set play state information
		# for functions related to cmif anchors
		self.played_url = self.url = self.armed_url
		self.played_str = self.armed_str
		self.play_node=node
		
		self.window.setanchorcallback(self.cbanchor)
		self.window.RetrieveUrl(url)
		self.window.setredrawfunc(self.redraw)

	def redraw(self):
		self.window.Refresh()

	def stopplay(self, node):
		if self.window and hasattr(self.window,'DestroyHtmlCtrl'):
			self.window.DestroyHtmlCtrl()
			self.window.setredrawfunc(None)
		Channel.ChannelWindow.stopplay(self, node)

#################################
	# helpers			
	def islocal(self,url):
		utype, url = MMurl.splittype(url)
		host, url = MMurl.splithost(url)
		return not utype and not host

	def toabs(self,url):
		if not self.islocal(url):
			return url
		filename=MMurl.url2pathname(MMurl.splithost(url)[1])
		if os.path.isfile(filename):
			if not os.path.isabs(filename):
				filename=os.path.join(os.getcwd(),filename)
				filename=ntpath.normpath(filename)	
		return filename
	
################################# imm node support with temp files
	def totemp(self,node,str):
		if node in self._tempmap.keys():
			filename=self._tempmap[node]
		else:
			import tempfile
			filename = tempfile.mktemp('.html')
			fp=open(filename,'wb')
			fp.write(str)
			fp.close()
			self._tempmap[node]=filename
		return filename

	def cleartemp(self):
		import win32api
		for f in self._tempmap.values():
			win32api.DeleteFile(f)

#################################
	def updatefixedanchors(self, node):
		if self._armstate != Channel.AIDLE or \
		   self._playstate != Channel.PIDLE:
			if self._played_node == node:
				# Ok, all is well, we've played it.
				return 1
			windowinterface.showmessage('Cannot recompute anchorlist (channel busy)')
			return 1
		windowinterface.setwaiting()
		context = Channel.AnchorContext()
		self.startcontext(context)
		save_syncarm = self.syncarm
		self.syncarm = 1
		self.arm(node)
		save_synplay = self.syncplay
		self.syncplay = 1
		self.play(node)
		self.stopplay(node)
		self.syncarm = save_syncarm
		self.syncplay = save_synplay
		windowinterface.setready()
		return 1
			
	def defanchor(self, node, anchor, cb):
		# Anchors don't get edited in the HtmlChannel.  You
		# have to edit the text to change the anchor.  We
		# don't want a message, though, so we provide our own
		# defanchor() method.
		apply(cb, (anchor,))

	def cbanchor(self, href):
		if href[:5] <> 'cmif:':
			self.www_jump(href, 'GET', None, None)
			return
		self.cbcmifanchor(href, None)

	def cbform(self, widget, userdata, calldata):
		if widget <> self.htmlw:
			raise 'kaboo kaboo'
		href = calldata.href
		list = map(lambda a,b: (a,b),
			   calldata.attribute_names, calldata.attribute_values)
		if not href or href[:5] <> 'cmif:':
			self.www_jump(href, calldata.method,
				      calldata.enctype, list)
			return
		self.cbcmifanchor(href, list)

	def cbcmifanchor(self, href, list):
		aname = href[5:]
		tp = self.findanchortype(aname)
		if tp == None:
			windowinterface.showmessage('Unknown CMIF anchor: '+aname)
			return
		if tp == ATYPE_PAUSE:
			f = self.pause_triggered
		else:
			f = self.anchor_triggered
		f(self.play_node, [(aname, tp)], list)

	def findanchortype(self, name):
		alist = MMAttrdefs.getattr(self.play_node, 'anchorlist')
		for aid, atype, args in alist:
			if aid == name:
				return atype
		return None

	def fixanchorlist(self, node):
		allanchorlist = [] #self.htmlw.GetHRefs()
		anchorlist = []
		for a in allanchorlist:
			if a[:5] == 'cmif:':
				anchorlist.append(a[5:])
		if len(anchorlist) == 0:
			return
		nodeanchorlist = MMAttrdefs.getattr(node, 'anchorlist')[:]
		oldanchorlist = map(lambda x:x[0], nodeanchorlist)
		newanchorlist = []
		for a in anchorlist:
			if a not in oldanchorlist:
				newanchorlist.append(a)
		if not newanchorlist:
			return
		for a in newanchorlist:
			nodeanchorlist.append(a, ATYPE_NORMAL, [])
		node.SetAttr('anchorlist', nodeanchorlist)
		MMAttrdefs.flushcache(node)


	#
	# The stuff below has little to do with CMIF per se, it implements
	# a general www browser
	#
	def www_jump(self, href, method, enctype, list):
		#
		# Check that we understand what is happening
		if enctype <> None:
			print 'HtmlChannel: unknown enctype:', enctype
			return
		if method not in (None, 'GET'):
			print 'HtmlChannel: unknown method:', method
			print 'href:', href
			print 'method:', method
			print 'enctype:', enctype
			print 'list:', list
			return
		if href:
			if href == 'XXXX:play/node':
				self.htmlw.insert_html(self.played_str, self.played_url)
				self.url = self.played_url
				return
			href = MMurl.basejoin(self.url, href)
		else:
			href = self.url
		if list:
			href = addquery(href, list)
		self.url, tag = MMurl.splittag(href)
		try:
			u = MMurl.urlopen(self.url)
			if u.headers.maintype == 'image':
				newtext = '<IMG SRC="%s">\n' % self.url
			else:
				newtext = u.read()
		except IOError:
			newtext = '<H1>Cannot Open</H1><P>'+ \
				  'Cannot open '+self.url+':<P>'+ \
				  `(sys.exc_type, sys.exc_value)`+ \
				  '<P>\n'
		footer = '<HR>[<A HREF="XXXX:play/node">BACK</A> to CMIF node]'
		self.htmlw.insert_html(newtext+footer, self.url)
##		self.htmlw.footerText = '<P>[<A HREF="'+self.armed_url+\
##			  '">BACK</A> to CMIF node]<P>'


image_cache = {}

def addquery(href, list):
	if not list: return href
	if len(list) == 1 and list[0][0] == 'isindex':
		query = encodestring(list[0][1])
	else:
		list = map(encodequery, list)
		list = map(lambda x:x[0]+'='+x[1], list)
		query = string.joinfields(list, '&')
	href = href + '?' + query
	return href

def encodequery(query):
	name, value = query
	name = encodestring(name)
	value = encodestring(value)
	return (name, value)

def encodestring(s):
	return MMurl.quote(s or '')	# Catches None as well!
