__version__ = "$Id$"

import os, posixpath
import sys
import string
import windowinterface
import MMAttrdefs, MMurl
from urlparse import urlparse, urlunparse
from MMExc import *
from EditMgr import EditMgr
from ViewDialog import ViewDialog
from Hlinks import *
from usercmd import *
import MMmimetypes
import urlcache
import features
import compatibility
import settings
import systemtestnames

# Mapping view numbers to view names and the reverse
VIEWNUM2NAME=[
	"player",
	"structure",
	"timeline",
	"links",
	"oldlayout",
	"customtests",
	"transitions",
	"layout",
	"source",
	"assets",
	"errors",
]
VIEWNAME2NUM={}
for i in range(len(VIEWNUM2NAME)): VIEWNAME2NUM[VIEWNUM2NAME[i]] = i

# an empty document
EMPTY = """
<smil>
  <head>
    <meta name="title" content="root-layout"/>
    <layout>
      <root-layout id="root-layout" title="root-layout" width="640" height="480"/>
    </layout>
  </head>
  <body>
  </body>
</smil>
"""

from TopLevelDialog import TopLevelDialog

Error = 'TopLevel.Error'

hasLayoutView2 = None

class TopLevel(TopLevelDialog, ViewDialog):
	def __init__(self, main, url, new_file):
		ViewDialog.__init__(self, 'toplevel_')
		self.prune = 0
		self.select_fdlist = []
		self.select_dict = {}
		self._last_timer_id = None
		self.main = main
		self.new_file = new_file
		utype, host, path, params, query, fragment = urlparse(url)
		dir, base = posixpath.split(path)
		if (not utype or utype == 'file') and \
		   (not host or host == 'localhost'):
			# local file
			self.dirname = dir
		else:
			# remote file
			self.dirname = ''
			# RTIPA start
			# add a query string with width/height/class parameters to URL
			if hasattr(features, 'RTIPA') and features.RTIPA and settings.get('RTIPA_add_params'):
				import socket
				width, height = windowinterface.getscreensize()
				query = 'width=%d&height=%d' % (width, height)
				try:
					hostname = settings.get('RTIPA_client_IP')
					ip = socket.gethostbyname(hostname)
				except socket.error:
					# host unknown
					pass
				else:
					ip = socket.inet_aton(ip)
					qos = settings.RTIPA_classes.get(ip)
					if qos is not None:
						query = query + '&class=' + qos
				if settings.get('RTIPA_debug'):
					windowinterface.showmessage('Adding query string "%s"' % query)
			# RTIPA end
		url = urlunparse((utype, host, path, params, query, None))
		if new_file:
			import MMmimetypes
			mtype = MMmimetypes.guess_type(url)[0]
		else:
			mtype = urlcache.mimetype(url)
		if mtype in ('application/x-grins-project', 'application/smil', 'application/x-grins-binary-project'):
			self.basename = posixpath.splitext(base)[0]
		else:
			self.basename = base
		self.filename = url
		self.window = None	# Created in TopLevelDialog.py

		self.create_commandlist()

		# we create only one edit manager per toplevel window.
		self.editmgr = EditMgr(self)
		self.editmgr.register(self)
		settings.register(self)

		try:
			# read the document		
			self.read_it()
			self.__checkInitialErrors()
		except:
			self.editmgr.unregister(self)
			settings.unregister(self)
			raise

		# when a document with errors, and if the user accept the errors,
		# the views are not relevant in this case. So we set a flag on the context to say
		# the don't show views (except the source view). It's an easy way to remember when you restore (with undo command)
		# the original document
		if not self.context.isValidDocument():
			self.context.disableviews = 1
		
		TopLevelDialog.__init__(self)
		self.makeviews()

	def __repr__(self):
		return '<TopLevel instance, url=' + `self.filename` + '>'

	# check the errors on the first load. And if any error, ask
	# the user whether he wants the editor to fix the errors
	# automatically. Note: this test is a bit different than the
	# test in the source view: if any error, there is no rollback
	def __checkInitialErrors(self, allowCancel = 1):
		context = self.root.GetContext()
		parseErrors = context.getParseErrors()
		if parseErrors is not None:
			if parseErrors.getType() == 'fatal':
				if features.SOURCE_VIEW_EDIT not in features.feature_set:
					# not allowed to edit, so signal syntax error
					raise MSyntaxError, '\n\n'+parseErrors.getFormatedErrorsMessage(1)
				message = 'The source document contains an unrecoverable error:\n\n' + \
					  parseErrors.getFormatedErrorsMessage(5) + \
					  '\nDo you want to edit the source file?'
				allowCancel = 0
				ret = windowinterface.GetYesNo(message, self.window)
				if ret != 0:
					raise MSyntaxError
				return
			else:
				message = "The source document contains "+`parseErrors.getErrorNumber()`+" errors: \n\n" + \
					  parseErrors.getFormatedErrorsMessage(5) + \
					  "\nShall I attempt to fix these?"
			if features.SOURCE_VIEW_EDIT not in features.feature_set:
				ret = 0	# automatically fix errors if not allowed to edit
				windowinterface.showmessage("The source document contains "+
							    `parseErrors.getErrorNumber()`+" errors: \n\n" + \
							    parseErrors.getFormatedErrorsMessage(5))
			elif allowCancel:
				ret = windowinterface.GetYesNoCancel(message, self.window)
			else:
				ret = windowinterface.GetYesNo(message, self.window)
			if ret == 0: # yes
				# accept the errors automatically fixed by GRiNS
				context.setParseErrors(None)
				self.changed = 1
			elif ret == 1: # no
				# default treatment: accept errors and don't allow to edit another view
				pass
			else: # cancel: raise an error: it will be intercepted
				raise MSyntaxError

	# detect the errors/fatal errors
	# if it's a fatal error, then load an empty document to keep GRiNS in a stable state
	def checkParseErrors(self, root):
		oldcontext = root.GetContext()
		parseErrors = oldcontext.getParseErrors()
		if parseErrors is not None and parseErrors.getType() == 'fatal':
			# XXX for now, if there is any fatal error, we load an empty document. In this case, we
			# even be able to edit the source view.
			baseurl = oldcontext.baseurl
			root.Destroy()
			import SMILTreeRead
			root = SMILTreeRead.ReadString(EMPTY, self.filename)
			# check that the 'EMPTY' document does't generate a fatal error as well
			# note: it shouldn't happen
			iParseErrors = root.GetContext().getParseErrors()
			if iParseErrors != None and iParseErrors.getType() == 'fatal':
				# re-raise
				raise MSyntaxError

			# if we reload the empty document we have to re-set the previous error and baseurl
			newcontext = root.GetContext()
			newcontext.setbaseurl(baseurl)
			newcontext.setParseErrors(parseErrors)
		return root
		
	def create_commandlist(self):
		self.commandlist = [
			RESTORE(callback = (self.restore_callback, ())),
			CLOSE(callback = (self.close_callback, ())),
			SOURCEVIEW(callback = (self.view_callback, (8, ))),
			HIDE_SOURCEVIEW(callback = (self.hide_view_callback, (8, ))),
			]

		self.viewcommandlist = [
			PLAY(callback = (self.play_callback, ())),
			PLAYERVIEW(callback = (self.view_callback, (0,))),
			HIERARCHYVIEW(callback = (self.view_callback, (1,))),
			PROPERTIES(callback = (self.prop_callback, ())),

			HIDE_PLAYERVIEW(callback = (self.hide_view_callback, (0,))),
			HIDE_HIERARCHYVIEW(callback = (self.hide_view_callback, (1,))),
			]
		self.markcommandlist = [
			MARK(callback = (self.mark_callback, ())),
		]

		if not features.lightweight:
			self.viewcommandlist = self.viewcommandlist + [
				LINKVIEW(callback = (self.view_callback, (3,))),
				LAYOUTVIEW(callback = (self.view_callback, (4,))),
				LAYOUTVIEW2(callback = (self.view_callback, (7, ))),
				ASSETSVIEW(callback = (self.view_callback, (9, ))),
				HIDE_LAYOUTVIEW2(callback = (self.hide_view_callback, (7, ))),
				HIDE_LINKVIEW(callback = (self.hide_view_callback, (3,))),
				HIDE_LAYOUTVIEW(callback = (self.hide_view_callback, (4,))),
				HIDE_USERGROUPVIEW(callback = (self.hide_view_callback, (5,))),
				HIDE_ASSETSVIEW(callback = (self.hide_view_callback, (9,))),
				]
			self.__ugroup = [
				TRANSITIONVIEW(callback = (self.view_callback, (6, ))),
				HIDE_TRANSITIONVIEW(callback = (self.hide_view_callback, (6, ))),
				]
			if features.USER_GROUPS in features.feature_set:
				self.__ugroup.append(USERGROUPVIEW(callback = (self.view_callback, (5,))))
		else:
			self.__ugroup = []


		# the error view command is showed only when errors
		self.errorscommandlist = [
			ERRORSVIEW(callback = (self.view_callback, (10, ))),
			HIDE_ERRORSVIEW(callback = (self.hide_view_callback, (10, ))),
			]

		self.undocommandlist = [
			UNDO(callback = (self.undo_callback, ())),
			REDO(callback = (self.redo_callback, ())),
			]

		if hasattr(self, 'do_edit'):
			self.commandlist.append(EDITSOURCE(callback = (self.edit_callback, ())))
		if self.main.cansave():
			self.savecommandlist = [
				SAVE(callback = (self.save_callback, ())),
				]
			self.publishcommandlist = [
				SAVE_AS(callback = (self.saveas_callback, ())),
				]
			if features.EXPORT_REAL in features.feature_set:
				self.publishcommandlist = self.publishcommandlist + [
					EXPORT_G2(callback = (self.bandwidth_callback, ('real', self.export_REAL_callback))),
					UPLOAD_G2(callback = (self.bandwidth_callback, ('real', self.upload_REAL_callback))),
					]
			if features.EXPORT_QT in features.feature_set:
				self.publishcommandlist = self.publishcommandlist + [
					EXPORT_QT(callback = (self.bandwidth_callback, ('qt', self.export_QT_callback))),
					UPLOAD_QT(callback = (self.bandwidth_callback, ('qt', self.upload_QT_callback))),
					]

			if features.EXPORT_WMP in features.feature_set:
				self.publishcommandlist = self.publishcommandlist + [
					EXPORT_WMP(callback = (self.bandwidth_callback, ('wmp', self.export_WMP_callback))),
##					UPLOAD_WMP(callback = (self.bandwidth_callback, ('wmp', self.upload_WMP_callback))),
					]
			if features.EXPORT_HTML_TIME in features.feature_set:
				self.publishcommandlist = self.publishcommandlist + [
					EXPORT_HTML_TIME(callback = (self.export_HTML_TIME_callback,())),
					]
			if features.EXPORT_SMIL2 in features.feature_set:
				self.publishcommandlist = self.publishcommandlist + [
					EXPORT_SMIL(callback = (self.bandwidth_callback, ('smil', self.export_SMIL2_callback,))),
					UPLOAD_SMIL(callback = (self.bandwidth_callback, ('smil', self.upload_SMIL2_callback,))),
					EXPORT_PRUNE(callback = (self.saveas_callback, (1,))),
					]
			if features.EXPORT_SMIL1 in features.feature_set:
				self.publishcommandlist = self.publishcommandlist + [
					EXPORT_SMIL1(callback = (self.export_SMIL1_callback, ())),
					]
##			if features.EXPORT_XMT in features.feature_set:
##				self.publishcommandlist = self.publishcommandlist + [
##					EXPORT_XMT(callback = (self.bandwidth_callback, ('xmt', self.export_XMT_callback,))),
##					UPLOAD_XMT(callback = (self.bandwidth_callback, ('xmt', self.upload_XMT_callback,))),
##					]
			if features.EXPORT_WINCE in features.feature_set:
				self.publishcommandlist = self.publishcommandlist + [
					EXPORT_WINCE(callback = (self.export_wince_callback, ())),
					]
		else:
			self.savecommandlist = self.publishcommandlist = []
		import Help
		if hasattr(Help, 'hashelp') and Help.hashelp():
			self.commandlist.append(
				HELP(callback = (self.help_callback, ())))

		# make the commandlist specific to the plateform
		TopLevelDialog.set_commandlist(self)
			
	def update_undocommandlist(self):
		commandlist = self.commandlist
		if not self.context.disableviews:
			commandlist = commandlist + self.viewcommandlist
			if self.context.attributes.get('project_boston', 0):
				commandlist = commandlist + self.__ugroup
		if self.context.isValidDocument():
			if self.changed:
				utype, host, path, params, query, fragment = urlparse(self.filename)
				if (not utype or utype == 'file') and (not host or host == 'localhost'):
					commandlist = commandlist + self.savecommandlist
			commandlist = commandlist + self.publishcommandlist
		else:
			commandlist = commandlist + self.errorscommandlist
		if self.editmgr.history:
			commandlist = commandlist + self.undocommandlist[:1]
		if self.editmgr.future:
			commandlist = commandlist + self.undocommandlist[1:]
		if self.player and self.hierarchyview and self.player.can_mark() and \
				self.hierarchyview.can_mark():
			commandlist = commandlist + self.markcommandlist

		self.setcommands(commandlist)

	def updateCommandlistOnErrors(self):
		self.update_undocommandlist()
		
	def show(self):
		TopLevelDialog.show(self)

		# This flag allow to know if the current views are disabled.
		# It's use the following raison: if you fix all errors after the initial state, you can easily known that
		# you have to turn on the views
		self.viewsdisabled = 0
		
		self.showviews()
		# A new file we immedeately save
		if self.new_file:
			self.saveas_callback()

		self.update_undocommandlist()
		
	def showdefaultviews(self):
		viewinfo = self.root.context.getviewinfo()
		if viewinfo is None:
			import settings
			viewinfo = settings.get('openviews')
		for viewname, geometry in viewinfo:
			viewnum = VIEWNAME2NUM[viewname]
			self.views[viewnum].set_geometry(geometry)
			self.views[viewnum].show()

	def saveviewgeometries(self):
		import settings
		if settings.get('saveopenviews'):
			viewinfo = self.getviewgeometries()
			settings.set('openviews', viewinfo)
		else:
			settings.delete('openviews')
		settings.save()

	def getviewgeometries(self):
		viewinfo = []
		for viewno in range(len(self.views)):
			v = self.views[viewno]
			if not v:
				continue
			info = v.get_geometry()
			if info:
				viewname = VIEWNUM2NAME[viewno]
				viewinfo.append((viewname, info))
##		for i in viewinfo: print 'VIEWINFO', i
		return viewinfo

	def destroy(self):
		self.set_timer(-1, None)
		self.hideviews()
		self.editmgr.clearclip()
		self.editmgr.unregister(self)
		settings.unregister(self)
		self.editmgr.destroy()
		self.destroyviews()
		self.hide()
		self.root.Destroy()
		for v in self.views:
			if v is not None:
				v.toplevel = None
		self.views = []
		if self in self.main.tops:
			self.main.tops.remove(self)

	def timer_callback(self, curtime):
		self._last_timer_id = None
		self.player.timer_callback(curtime)

	def set_timer(self, delay, arg):
		if self._last_timer_id is not None:
			windowinterface.canceltimer(self._last_timer_id)
			self._last_timer_id = None
		if delay >= 0:
			self._last_timer_id = windowinterface.settimer(delay,
				  (self.timer_callback, (arg,)))

	#
	# View manipulation.
	#
	def makeviews(self):
		# Reads settings from features.py and loads whichever views are needed..
		self.channelview = None	# XXX to be removed eventually
		self.layoutview = None
		self.ugroupview = None
		self.player = None
		self.hierarchyview = None
		self.links = None
		self.layoutview2 = None
		self.transitionview = None
		self.sourceview = None
		self.assetsview = None
		self.errorsview = None

		if features.STRUCTURE_VIEW in features.feature_set:
			import HierarchyView
			self.hierarchyview = HierarchyView.HierarchyView(self)

		if features.PLAYER_VIEW in features.feature_set:
			import Player
			self.player = Player.Player(self)

		if features.TRANSITION_VIEW in features.feature_set:
			import TransitionView
			self.transitionview = TransitionView.TransitionView(self)

		if features.LAYOUT_VIEW in features.feature_set:
			global hasLayoutView2
			if hasLayoutView2 is None or hasLayoutView2:
				try:
					import LayoutView2
				except (ImportError, AttributeError):
					hasLayoutView2 = 0
					self.layoutview2 = None
				else:
					hasLayoutView2 = 1
					self.layoutview2 = LayoutView2.LayoutView2(self)
			else:
				self.layoutview2 = None

		if features.HYPERLINKS_VIEW in features.feature_set:
			import LinkEdit
			self.links = LinkEdit.LinkEdit(self)
		else:
			import LinkEditLight
			self.links = LinkEditLight.LinkEditLight(self)

		if features.USER_GROUPS in features.feature_set:
			import UsergroupView
			self.ugroupview = UsergroupView.UsergroupView(self)
			
		if features.SOURCE_VIEW in features.feature_set:
			import SourceView
			self.sourceview = SourceView.SourceView(self)

		if features.ERRORS_VIEW in features.feature_set:
			# for now, this view is not supported on all plateform
			try:
				import ErrorsView
				self.errorsview = ErrorsView.ErrorsView(self)
			except (ImportError, AttributeError):
				self.errorsview = None

		if features.ASSETS_VIEW in features.feature_set:
			import AssetsView
			self.assetsview = AssetsView.AssetsView(self)

		# Views that are destroyed by restore (currently all)
		# Notice that these must follow the order of
		# VIEWNUM2NAME.
		self.views = [self.player, self.hierarchyview,
			      self.channelview, self.links, self.layoutview,
			      self.ugroupview, self.transitionview, self.layoutview2,
			      self.sourceview, self.assetsview, self.errorsview
			      ]

	def hideviews(self):
		for v in self.views:
			if v is not None:
				v.hide()

	def destroyviews(self):
		for v in self.views:
			if v is not None:
				v.destroy()

	def checkviews(self):
		pass

	#
	# Callbacks.
	#
	def undo_callback(self):
		self.editmgr.undo()

	def redo_callback(self):
		self.editmgr.redo()

	def play_callback(self):
#		self.player.show((self.player.playsubtree, (self.root,)))
		self.player.play_callback()

	def pause_callback(self):
		self.player.pause_callback()

	def stop_callback(self):
		self.player.stop_callback()

	def mark_callback(self):
		self.hierarchyview.mark_callback()

	def save_source_callback(self, text):
		# This is a function that is called from the source view when the user decides to save.
		# Compare to edit_finished_callback, which is when a temporary file is used for the sourceview.
		if self.editmgr.busy:
			print "Warning! Source view trying to save during an editmgr transaction."
		showing = []
		for i in range(len(self.views)):
			if self.views[i] is not None and \
					self.views[i].is_showing():
				geom = self.views[i].get_geometry()
				showing.append((i, geom))
		self.editmgr.clearclip()  # Not optimal, but there is little we can do about it...
		self.editmgr.unregister(self)
		self.editmgr.destroy() # kills subscribed views
		self.context.seteditmgr(None)
		self.root.Destroy()

		# Now we actually read the text.
		self.do_read_it_from_string(text)

		self.context = self.root.GetContext()
		self.editmgr = EditMgr(self.root)
		self.context.seteditmgr(self.editmgr)
		self.editmgr.register(self)
		self.makeviews()

		self.showviews(showing)
		
		self.changed = 1
		self.update_undocommandlist()
		
	def view_callback(self, viewno):
		self.setwaiting()
		view = self.views[viewno]
		if view is not None:
			view.show()
		else:
			windowinterface.showmessage('View does not exist!', mtype = 'error', parent = self.window)

	# load a source file without affect the current root
	# return the new root
	def load_source(self, text):		
		# init progress bar dialog
		self.progress = windowinterface.ProgressDialog("Reloading")
		self.progressMessage = "Reloading SMIL document from source view..."
		self.progress.set(self.progressMessage)

		baseurl = self.root.GetContext().baseurl
		# read the source and update edit manager
		try:
			import SMILTreeRead		
			root = SMILTreeRead.ReadString(text, self.filename, self.printfunc, progressCallback = (self.progressCallback, 0.5))
		except (UserCancel, IOError):				
			# the progress dialog will disappear
			self.progress = None
			# re-raise
			raise

		root.GetContext().setbaseurl(baseurl)

		# just update that the loading is finished
		self.progressCallback(1.0)

		# the progress bar will desapear
		self.progress = None
						
		# return the new root
		return root
		
	def hide_view_callback(self, viewno):
		view = self.views[viewno]
		if view is not None and view.is_showing():
			view.hide()

	def getsettingsdict(self):
		# Returns the initializer dictionary used
		# to create the toolbar pulldown menus for
		# preview playback preferences

		alltests = self.root.GetAllSystemTests()
		# Special case: if we are showing bandwidths in the
		# structure view we always show the bitrate popup.
		if not 'system_bitrate' in alltests and self.root.showtime == 'bwstrip':
			alltests.append('system_bitrate')
		dict = {}
		for testname in alltests:
			exttestname = systemtestnames.int2extattr(testname)
			val = settings.get(testname)
			values = systemtestnames.getallexternal(testname)
			init = systemtestnames.int2extvalue(testname, val)
			dict[exttestname] = (values, (self.systemtestcb, testname), init)
		# Add the "synchronous playback" button
		offon = ['off', 'on']
		cur = offon[settings.get('default_sync_behavior_locked')]
		dict['Synchronous playback'] = (offon, self.syncmodecb, cur)
		return dict

	def syncmodecb(self, arg):
		settings.set('default_sync_behavior_locked', arg == 'on')

	def update_toolbarpulldowns(self):
		self.setsettingsdict(self.getsettingsdict())

	def systemtestcb(self, attrname, extvalue):
		attrvalue = systemtestnames.ext2intvalue(attrname, extvalue)
		if settings.get(attrname) != attrvalue:
			settings.set(attrname, attrvalue)
			self.root.ResetPlayability()
		return 1		# indicate success

	def save_callback(self):
		if self.new_file:
			self.saveas_callback()
			return
		utype, host, path, params, query, fragment = urlparse(self.filename)
		if (utype and utype != 'file') or (host and host != 'localhost'):
			windowinterface.showmessage('Cannot save to nonlocal URL.',
						    mtype = 'error')
			return
		file = MMurl.url2pathname(path)
		self.setwaiting()
		ok = self.save_to_file(file)

	def saveas_okcallback(self, filename):
		if not filename:
			return 'no file specified'
		self.setwaiting()
		if self.save_to_file(filename):
			if self.closeonsave:
				self.close()
				return 1
			self.filename = MMurl.pathname2url(filename)
##			self.context.setbaseurl(self.filename)
			self.fixtitle()
		else:
			return 1

	def saveas_callback(self, prune = 0, close = 0):
		if self.new_file:
			cwd = settings.get('savedir')
		else:
			cwd = self.dirname
			if cwd:
				cwd = MMurl.url2pathname(cwd)
				if not os.path.isabs(cwd):
					cwd = os.path.join(os.getcwd(), cwd)
			else:
				cwd = os.getcwd()
		title = 'Save GRiNS project:'
		filetypes = ['application/x-grins-project', 'application/x-grins-binary-project']
		if prune:
			filetypes = ['application/smil']
			title = 'Save SMIL file:'
			self.prune = 1
		dftfilename = ''
		if self.filename:
			utype, host, path, params, query, fragment = urlparse(self.filename)
			dftfilename = os.path.split(MMurl.url2pathname(path))[-1]
		self.closeonsave = close
		windowinterface.FileDialog(title, cwd, filetypes,
					   dftfilename, self.saveas_okcallback, None)

	def export_okcallback(self, filename):
		exporttype = self.exporttype
			
		if not filename:
			return 'no file specified'
		self.setwaiting()
		license = self.main.wanttosave()
		if not license:
			windowinterface.showmessage('Cannot obtain a license to save.', mtype='error')
			return
		evallicense= (license < 0)
		if not self.save_to_file(filename, exporting = 1):
			return		# Error, don't save HTML file
		if exporttype in ('SMIL1', 'SMIL2', 'WINCE'):
			return		# don't create HTML file for SMIL export
		attrs = self.context.attributes
		if not attrs.has_key('project_html_page') or not attrs['project_html_page']:
			if features.lightweight:
				attrs['project_html_page'] = 'external_player.html'
			# In the full version we continue, and the user gets a warning later (in HTMLWrite)
		#
		# Invent HTML file name and SMIL file url, and generate webpage
		#
		htmlfilename = os.path.splitext(filename)[0] + '.html'
		smilurl = MMurl.pathname2url(filename)

		# Make a back-up of the original file...
		oldhtmlfilename = ''
		try:
			oldhtmlfilename = make_backup_filename(htmlfilename)
			os.rename(htmlfilename, oldhtmlfilename)
		except os.error:
			pass
		try:
			import HTMLWrite
			HTMLWrite.WriteFile(self.root, htmlfilename, smilurl, oldhtmlfilename,
						evallicense=evallicense, exporttype=exporttype)
		except IOError, msg:
			windowinterface.showmessage('HTML export failed:\n%s'%(msg,))

	def bandwidth_callback(self, exporttype, do_export_callback):
		if exporttype == 'real':
			import settings
			import BandwidthCompute
			bandwidth = settings.get('system_bitrate')
			if bandwidth > 1000000:
				bwname = "%dMbps"%(bandwidth/1000000)
			elif bandwidth % 1000 == 0:
				bwname = "%dkbps"%(bandwidth/1000)
			else:
				bwname = "%dbps"%bandwidth
			msg = 'Computing bandwidth usage at %s...'%bwname
			dialog = windowinterface.BandwidthComputeDialog(msg)
			bandwidth, prerolltime, delaycount, errorseconds, errorcount , stalls = \
				BandwidthCompute.compute_bandwidth(self.root)
			dialog.setinfo(prerolltime, errorseconds, delaycount, errorcount)
			dialog.done(do_export_callback, cancancel=1)
		else:
			# For other export types we don't know how to calculate bandwidth
			# usage (yet)
			do_export_callback()

	def export_REAL_callback(self):
		self.export('REAL')
		
	def export_QT_callback(self):
		self.export('QuickTime')

	def export_SMIL2_callback(self):
		self.export('SMIL2')

	def export_SMIL1_callback(self):
		self.export('SMIL1')

	def export_XMT_callback(self):
		self.export('XMT')

	def export_wince_callback(self):
		self.export('WINCE')

	def export_WMP_callback(self):
		import wmpsupport
		if wmpsupport.haswmpruntimecomponents():
			cwd = self.dirname
			if cwd:
				cwd = MMurl.url2pathname(cwd)
				if not os.path.isabs(cwd):
					cwd = os.path.join(os.getcwd(), cwd)
			else:
				cwd = os.getcwd()
			basename = self.basename + ".wmv"
			windowinterface.FileDialog('Export to WMP file:', cwd, 'video/x-ms-wmv',
						basename, self.export_WMP_okcallback, None)
		else:
			windowinterface.showmessage('No WMP export components on this system.')
	
	def export_WMP_okcallback(self, pathname):
		import wmpsupport
		wmpsupport.Exporter(pathname, self.player)

	def export_HTML_TIME_callback(self):
		cwd = self.dirname
		if cwd:
			cwd = MMurl.url2pathname(cwd)
			if not os.path.isabs(cwd):
				cwd = os.path.join(os.getcwd(), cwd)
		else:
			cwd = os.getcwd()
		basename = self.basename + '.html'
		windowinterface.FileDialog('Export to HTML+TIME file:', cwd, 'text/html',
					basename, self.export_HTML_TIME_okcallback, None)
	
	def export_HTML_TIME_okcallback(self, pathname):
		if self.player: self.player.stop_callback()
		self.export_to_html_time(pathname)
		if sys.platform=='win32':
			# Hardcoded for now. Should be read from the registry
			iepath = r'C:\Program Files\Internet Explorer'
			iepath = os.path.join(iepath, 'iexplore.exe')
			try:
				import win32api
				win32api.WinExec(iepath + ' ' + pathname)
			except:
				pass


	def export(self, exporttype):
		self.exporttype = exporttype

		# TODO: this also has to handle WMP -mjvdg.

		# If new, we ask
		if not self.new_file:
			# If we have a project file name, use it
			if urlcache.mimetype(self.filename) == 'application/x-grins-project':
				utype, host, path, params, query, fragment = urlparse(self.filename)
				# If the project file is remote, we ask for filename.
				if (not utype or utype == 'file') and (not host or host == 'localhost'):
					# don't ask for a filename
					file = MMurl.url2pathname(path)
					base = os.path.splitext(file)[0]
					file = base + MMmimetypes.guess_extension('application/smil')
					self.setwaiting()
					self.export_okcallback(file)
					return

		# ask for a filename
		cwd = self.dirname
		if cwd:
			cwd = MMurl.url2pathname(cwd)
			if not os.path.isabs(cwd):
				cwd = os.path.join(os.getcwd(), cwd)
		else:
			cwd = os.getcwd()
		windowinterface.FileDialog('Publish SMIL file:', cwd, 'application/smil',
					   '', self.export_okcallback, None)
	   
	def upload_REAL_callback(self):
		self.upload('REAL')
		
	def upload_QT_callback(self):
		self.upload('QuickTime')

	def upload_SMIL2_callback(self):
		self.upload('SMIL2')

	def upload_XMT_callback(self):
		self.upload('XMT')

	def upload_WMP_callback(self):
		self.upload('WMP')

	def upload(self, exporttype):
		self.exporttype = exporttype
		# TODO: this also has to handle WMP.
		
		# XXXX The filename business confuses project file name and resulting SMIL file
		# XXXX name. To be fixed.
		#
		# XXXX The multi-stage password asking code here is ugly.
		if not self.filename:
			windowinterface.showmessage('Cannot upload unsaved document.\nPlease save first.')
			return
		filename, smilurl, weburl, self.w_ftpinfo, self.m_ftpinfo = self.get_upload_info()
			
		missing = ''
		attr = None
		attrs = self.context.attributes
		# REAL and QT products require a web page
		hlinks = self.context.hyperlinks
		have_local_links = 0
		for a1 in self.root.getanchors(1):
			for link in hlinks.findalllinks(a1, None):
				a2 = link[ANCHOR2]
				if type(a2) is type(''):
					utype, host, path, params, query, fragment = urlparse(a2)
					if (not utype or utype == 'file') and (not host or host == 'localhost'):
						have_local_links = 1
						break

		if exporttype in ('REAL', 'QuickTime'):
			have_web_page = 1
		else:
			have_web_page = attrs.has_key('project_html_page')
		if have_web_page or have_local_links:
			if not self.w_ftpinfo[0]:
				attr = 'project_ftp_host'
				missing = '\n- Webserver FTP info'
			if have_web_page and not smilurl:
				if not attr: attr = 'project_smil_url'
				missing = missing + '\n- Mediaserver SMILfile URL'
			if have_local_links and not weburl:
				if not attr: attr = 'project_web_url'
				missing = missing + '\n- Webserver URL'
			if have_web_page and not attrs.get('project_html_page'):
				if features.lightweight:
					attrs['project_html_page'] = 'external_player.html'
				else:
					if not attr: attr = 'project_html_page'
					missing = missing + '\n- HTML Template'
		else:
			# We only have to check mediaserver params (we don't generate a webpage)
			if not self.m_ftpinfo[0]:
				attr = 'project_ftp_host_media'
				missing = '\n- Mediaserver FTP info'

		if missing:
			if windowinterface.showquestion('Document properties needed but not set:'+missing+
					'\n\nDo you want to set these?'):
				self.prop_callback(attr)
			return
		if have_web_page:
			# Do a sanity check on the SMILfile URL
			fn = MMurl.url2pathname(smilurl.split('/')[-1])
			if os.path.split(filename)[1] != os.path.split(fn)[1]:
				# The SMIL upload filename and URL don't match. Warn.
				if not windowinterface.showquestion('Warning: Mediaserver SMIL URL appears incorrect:\n'+smilurl+'\nContinue anyway?'):
					return
		hostname, username, passwd, dirname = self.w_ftpinfo
		if username and not passwd:
			windowinterface.InputDialog('Enter password for %s at %s'%(username, hostname),
					'', self.upload_callback_2, passwd=1)
		else:
			self.upload_callback_2(passwd)
			
	def upload_callback_2(self, passwd):
		# This is the website password. See whether we also have to ask for the
		# media site password
		# Note that if we don't generate HTML we've set the two _ftpinfo sets to be the
		# same, so we never ask for a second password.
		w_hostname, w_username, dummy, w_dirname = self.w_ftpinfo
		m_hostname, m_username, m_passwd, m_dirname = self.m_ftpinfo
		self.w_ftpinfo = w_hostname, w_username, passwd, w_dirname
		if m_hostname == w_hostname and m_username == w_username:
			self.upload_callback_3(passwd)
		elif m_username and not m_passwd:
			windowinterface.InputDialog('Enter password for %s at %s'%(m_username, m_hostname),
					'', self.upload_callback_3, passwd=1)
		else:
			self.upload_callback_3(m_passwd)
	
	def upload_callback_3(self, passwd):
		# Third stage of upload: we have the passwords
		m_hostname, m_username, dummy, m_dirname = self.m_ftpinfo
		self.m_ftpinfo = m_hostname, m_username, passwd, m_dirname
		filename, smilurl, weburl, d1, d2  = self.get_upload_info()
		self.save_to_ftp(filename, smilurl, weburl, self.w_ftpinfo, self.m_ftpinfo)
		del self.w_ftpinfo
		del self.m_ftpinfo
		
	def get_upload_info(self, w_passwd='', m_passwd=''):
		attrs = self.context.attributes
		have_web_page = attrs.has_key('project_html_page')

		# Mediasite FTP params
		m_hostname = ''
		m_username = ''
		m_dirname = ''
		if attrs.has_key('project_ftp_host_media'):
			m_hostname = attrs['project_ftp_host_media']
		if attrs.has_key('project_ftp_user_media'):
			m_username = attrs['project_ftp_user_media']
		if attrs.has_key('project_ftp_dir_media'):
			m_dirname = attrs['project_ftp_dir_media']

		# Website FTP parameters
		w_hostname = ''
		w_username = ''
		w_dirname = ''
		if attrs.has_key('project_ftp_host'):
			w_hostname = attrs['project_ftp_host']
		if attrs.has_key('project_ftp_user'):
			w_username = attrs['project_ftp_user']
		if attrs.has_key('project_ftp_dir'):
			w_dirname = attrs['project_ftp_dir']

		# Website FTP params default to Mediasite FTP parameters
		if not w_hostname:
			w_hostname = m_hostname
		if not w_username:
			w_username = m_username
		if not w_dirname:
			w_dirname = m_dirname

		# Filename for SMIL file on media site
		# XXXX This may be wrong, because it uses the "project" filename
		utype, host, path, params, query, fragment = urlparse(self.filename)
		dir, filename = posixpath.split(path)
		filename = posixpath.splitext(filename)[0] + \
			   MMmimetypes.guess_extension('application/smil')
		
		# URL of the SMIL file as it appears on the net
		smilurl = attrs.get('project_smil_url', '')

		# URL of the directory of the webpage as it appears on the net
		weburl = attrs.get('project_web_url')
		if weburl:
			if weburl[-1:] != '/':
				weburl = weburl + '/'
		else:
			# use directory part of smilurl as default for weburl
			utype, host, path, params, query, fragment = urlparse(smilurl)
			weburl = urlunparse((utype, host, path[:path.rfind('/')+1], '', '', '')) # includes final /

		return (filename, smilurl, weburl,
				(w_hostname, w_username, w_passwd, w_dirname), 
				(m_hostname, m_username, m_passwd, m_dirname))

	def prop_callback(self, initattr = None):
		import AttrEdit
		AttrEdit.showdocumentattreditor(self, initattr = initattr)

	#
	# support for external text editor (mac and unix)
	#
	
	def edit_callback(self):
		if not self.editmgr.transaction():
			return
		self.setwaiting()
		import SMILTreeWrite, tempfile
		# XXXX This is wrong, probably
		tmp = tempfile.mktemp(MMmimetypes.guess_extension('application/x-grins-project'))
		self.__edittmp = tmp
		SMILTreeWrite.WriteFile(self.root, tmp)
		self.do_edit(tmp)

	def edit_finished_callback(self, tmp = None):
		self.editmgr.rollback()
		if tmp is None:
			try:
				os.unlink(self.__edittmp)
			except os.error:
				pass
			del self.__edittmp
			return
		showing = []
		for i in range(len(self.views)):
			if self.views[i] is not None and \
					self.views[i].is_showing():
				geom = self.views[i].get_geometry()
				showing.append((i, geom))
#		self.editmgr.unregister(self)
#		self.editmgr.destroy() # kills subscribed views
#		self.context.seteditmgr(None)
		self.editmgr.clearclip() # Not sure this is needed...
		self.root.Destroy()
		save_new = self.new_file
		self.new_file = 1
		self.do_read_it(tmp)	# Reads the file and creates the MMNode heirarchy.
		self.root = self.checkParseErrors(self.root)
		self.setRoot(self.root)
		self.new_file = save_new
		try:
			os.unlink(self.__edittmp)
		except os.error:
			pass
		del self.__edittmp
#		self.context = self.root.GetContext()
#		self.editmgr = EditMgr(self.root)
#		self.context.seteditmgr(self.editmgr)
#		self.editmgr.register(self)
		self.makeviews()

		self.showviews(showing)

		self.changed = 1
		self.update_undocommandlist()

	#
	#
	#

	def fixtitle(self):
		utype, host, path, params, query, fragment = urlparse(self.filename)
		dir, base = posixpath.split(path)
		if (not utype or utype == 'file') and \
		   (not host or host == 'localhost'):
			# local file
			self.dirname = dir
		else:
			# remote file
			self.dirname = ''
		mtype = urlcache.mimetype(self.filename)
		if mtype in ('application/x-grins-project', 'application/smil', 'application/x-grins-binary-project'):
			self.basename = posixpath.splitext(base)[0]
		else:
			self.basename = base
		self.window.settitle(MMurl.unquote(self.basename))
		for v in self.views:
			if v is not None:
				v.fixtitle()

	def pre_save(self):
		# Get rid of hyperlinks outside the current tree and clipboard
		# (XXX We shouldn't *save* the links to/from the clipboard,
		# but we don't want to throw them away either...)
		roots = [self.root]
		data = self.root.context.editmgr.getclip()
		for node in data:
			if node.getClassName() == 'MMNode':
				roots.append(node)
		self.context.sanitize_hyperlinks(roots)
		# Get all windows to save their current geometry.
		# This is only really needed for TopLayouts now.
		for v in self.views:
			if v is not None:
				v.get_geometry()
				v.save_geometry()
		viewinfo = self.getviewgeometries()
		self.root.context.setviewinfo(viewinfo)
		

	def save_to_file(self, filename, exporting = 0):
		license = self.main.wanttosave()
		if not license:
			windowinterface.showmessage('Cannot obtain a license to save.')
			return 0
		evallicense= (license < 0)
		url = MMurl.pathname2url(filename)
		mimetype = MMmimetypes.guess_type(url)[0]
		if exporting and mimetype != 'application/smil':
			windowinterface.showmessage('Publish to SMIL (*.smi or *.smil) files only.')
			return
		if mimetype == 'application/smil':
			if not exporting:
				answer = windowinterface.GetOKCancel('GRiNS-specific information will be lost if you save your project as SMIL.')
				if answer != 0:
					return
		else:
			# Save a grins project file
			pass
		self.pre_save()
		# Make a back-up of the original file...
		try:
			os.rename(filename, make_backup_filename(filename))
		except os.error:
			pass
		settings.set('savedir', os.path.dirname(filename))

		if exporting:
			exporttype = self.exporttype
			grinsExt = 0
			copyfiles = 1
			qtExt = 0
			rpExt = 0
			pss4Ext = 0
			smil_one = 0
			convertfiles = 0
			addattrs = 0
			if exporttype == 'REAL':
				rpExt = 1
				convertfiles = 1
			elif exporttype == 'QuickTime':
				qtExt = 1
			elif exporttype == 'SMIL1':
				smil_one = 1
			elif exporttype == 'WINCE':
				addattrs = 1
				grinsExt = 1
				pss4Ext = 1
			# XXX enabling this currently crashes the application on Windows during video conversion
			progress = windowinterface.ProgressDialog("Publishing", self.cancel_upload)
			progress.set('Publishing document...')
			progress = progress.set
		else:
			grinsExt = mimetype != 'application/smil'
			qtExt = features.EXPORT_QT in features.feature_set
			rpExt = features.EXPORT_REAL in features.feature_set
			pss4Ext = 0
			smil_one = 0
			copyfiles = 0
			convertfiles = 0
			progress = None
			exporttype = None
			addattrs = 0

		if mimetype == 'application/x-grins-binary-project':
			import QuickWrite
			QuickWrite.WriteFile(self.root, filename)
		else:
			try:
				import SMILTreeWrite
				try:
					SMILTreeWrite.WriteFile(self.root, filename,
								grinsExt = grinsExt,
								qtExt = qtExt,
								rpExt = rpExt,
								pss4Ext = pss4Ext,
								copyFiles = copyfiles,
								convertfiles = convertfiles,
								convertURLs = 1,
								evallicense = evallicense,
								progress = progress,
								prune = self.prune,
								smil_one = smil_one,
								addattrs = addattrs)
				finally:
					self.prune = 0
			except IOError, msg:
				if exporting:
					operation = 'Publish'
				else:
					operation = 'Save'
				windowinterface.showmessage('%s failed:\n%s'%(operation, msg))
				return 0
			except KeyboardInterrupt:
				# Clear exception:
				try:
					raise 'foo'
				except:
					pass
				windowinterface.showmessage('Publish interrupted.')
				return 0
		if sys.platform == 'mac':
			import macostools
			macostools.touched(filename)
		if not exporting:
			self.main._update_recent(MMurl.pathname2url(filename))
			self.changed = 0
			self.new_file = 0
		self.update_undocommandlist()
		return 1
		
	def save_to_ftp(self, filename, smilurl, weburl, w_ftpparams, m_ftpparams):
		license = self.main.wanttosave()
		if not license:
			windowinterface.showmessage('Cannot obtain a license to save.')
			return 0
		evallicense= (license < 0)
		self.pre_save()
		have_web_page = (self.exporttype in ('REAL', 'QuickTime'))

		#
		# Export params
		#
		exporttype = self.exporttype
		qtExt = 0
		rpExt = 0
		smil_one = 0
		convertfiles = 0
		if exporttype == 'REAL':
			rpExt = 1
			convertfiles = 1
		elif exporttype == 'QuickTime':
			qtExt = 1
		elif exporttype == 'SMIL1':
			smil_one = 1
		#
		# Progress dialog
		#
		progress = windowinterface.ProgressDialog("Uploading", self.cancel_upload)
		progress.set("Generating document...")

		#
		# First save and upload the SMIL file (and the data items)
		#
		try:
			import SMILTreeWrite
			try:
				SMILTreeWrite.WriteFTP(self.root, filename, m_ftpparams, w_ftpparams,
						       grinsExt = 0,
						       qtExt = qtExt,
						       rpExt = rpExt,
						       copyFiles = 1,
						       convertfiles = convertfiles,
						       convertURLs = 1,
						       evallicense = evallicense,
						       progress = progress.set,
						       prune = self.prune,
						       smil_one = smil_one,
						       weburl = weburl)
			finally:
				self.prune = 0
		except IOError, msg:
			windowinterface.showmessage('Media upload failed:\n%s'%(msg,))
			return 0
		except KeyboardInterrupt:
			# Clear exception:
			try:
				raise 'foo'
			except:
				pass
			windowinterface.showmessage('Upload interrupted.')
			return 0
		if have_web_page:
			#
			# Next create and upload the HTML and RAM files
			#
			progress.set("Uploading webpage")
			#
			# Invent HTML file name and SMIL file url, and generate webpage
			#
			htmlfilename = os.path.splitext(filename)[0] + '.html'
			# XXXX We should generate from the previously saved HTML file
			oldhtmlfilename = ''
			try:
				import HTMLWrite
				HTMLWrite.WriteFTP(self.root, htmlfilename, smilurl, w_ftpparams, oldhtmlfilename,
							evallicense=evallicense, exporttype = self.exporttype)
			except IOError, msg:
				windowinterface.showmessage('Webpage upload failed:\n%s'%(msg,))
				return 0
			except KeyboardInterrupt:
				windowinterface.showmessage('Upload interrupted.')
				return 0
		# Is this needed?? (Jack)
		self.update_undocommandlist()
		return 1
		
	def cancel_upload(self):
		raise KeyboardInterrupt

	def export_to_html_time(self, filename):
		license = self.main.wanttosave()
		if not license:
			windowinterface.showmessage('Cannot obtain a license to save.')
			return 0
		evallicense= (license < 0)
		url = MMurl.pathname2url(filename)
		mimetype = MMmimetypes.guess_type(url)[0]
		if mimetype != 'text/html':
			windowinterface.showmessage('Publish to HTML (*.htm or *.html) files only.')
			return
		self.pre_save()
		try:
			progress = windowinterface.ProgressDialog("Publishing", self.cancel_upload)
			progress.set('Publishing document...')
			progress = progress.set
			import SMILTreeWriteXhtmlSmil
			SMILTreeWriteXhtmlSmil.WriteFileAsXhtmlSmil(self.root, filename,
						cleanSMIL = 1,
						grinsExt = 0,
						copyFiles = 0,
						evallicense=evallicense,
						progress = progress,
						convertURLs = 1)
		except IOError, msg:
			operation = 'Publish'
			windowinterface.showmessage('%s failed:\n%s'%(operation, msg))
			return 0
		except KeyboardInterrupt:
			# Clear exception:
			try:
				raise 'foo'
			except:
				pass
			windowinterface.showmessage('Publish interrupted.')
			return 0
		return 1

	def restore_callback(self):
		if self.changed or (self.sourceview != None and self.sourceview.is_changed()):
			windowinterface.showmessage(
				'This will discard all changes since the last save.\n\n'+
				'Are you sure you want to do this?',
				mtype = 'question',
				callback = (self.do_restore, ()),
				title = 'Revert to saved?')
			return
		self.do_restore()

	def do_restore(self):
#		if not self.editmgr.transaction():
#			return
		self.setwaiting()
		# keep the showing state of all current views
		showing = []
		for i in range(len(self.views)):
			if self.views[i] is not None and \
					self.views[i].is_showing():
				geom = self.views[i].get_geometry()
				showing.append((i, geom))
#		self.editmgr.rollback()
		# cleanup
		self.editmgr.clearclip()
		self.editmgr.unregister(self)
		self.editmgr.destroy() # kills subscribed views
		self.context.seteditmgr(None)
		self.destroyRoot(self.root)

		# editmgr have to be re-created. 		
		self.editmgr = EditMgr(self)
		self.editmgr.register(self)

		# read the document		
		self.read_it(isReloading=1)

		# check initial errors, and don't allow cancel
		self.__checkInitialErrors(0)

		if not self.context.isValidDocument():
			self.context.disableviews = 1
			
		# update command list, re-make the views, and show the views prviously showed		
		self.update_undocommandlist()
		
		self.makeviews()

		self.showviews(showing)

	def read_it(self, isReloading=0):
		self.changed = 0
		if self.new_file:
			if type(self.new_file) == type(''):
				self.do_read_it(self.new_file, isReloading)
			else:
				import SMILTreeRead
				self.root = SMILTreeRead.ReadString(EMPTY, self.filename)
			user = settings.get('license_user')
			if user[:13] == 'Licensed to: ':
				user = user[13:]
			if user:
				self.root.GetContext().attributes['author'] = user
		else:
			self.do_read_it(self.filename, isReloading)
		self.root = self.checkParseErrors(self.root)
		self.setRoot(self.root)
		if self.new_file:
			self.context.baseurl = ''
			if type(self.new_file) == type(''):
				self.context.template = self.new_file

	def progressCallback(self, pValue):
		self.progress.set(self.progressMessage, None, None, pValue*100, 100)
		
	def do_read_it(self, filename, isReloading=0):
##		import time
##		print 'parsing', filename, '...'
##		t0 = time.time()
		mtype = urlcache.mimetype(filename)
		if mtype not in ('application/x-grins-project', 'application/smil', 'application/x-grins-binary-project'):
			if windowinterface.showquestion('MIME type not application/smil or application/x-grins-project.\nOpen as SMIL document anyway?'):
				mtype = 'application/smil'
		if mtype in ('application/smil', 'application/x-grins-project'):
			import SMILTreeRead
			# init progress dialog
			if mtype == 'application/smil':
				self.progress = windowinterface.ProgressDialog("Import")
				self.progressMessage = "Importing SMIL document..."
			else:
				self.progress = windowinterface.ProgressDialog("Loading")
				self.progressMessage = "Loading GRiNS document..."				
			self.progress.set(self.progressMessage)
			
			check_compatibility = mtype == 'application/x-grins-project' and not isReloading
			try:
				self.root = SMILTreeRead.ReadFile(filename, self.printfunc, self.new_file, check_compatibility, \
												  progressCallback=(self.progressCallback, 0.5))
			except (UserCancel, IOError):
				# the progress dialog will disappear
				self.progress = None
				# re-raise
				raise

			ctx = self.root.GetContext()
			if hasattr(ctx, 'enableSave') and ctx.enableSave:
				# enableSave can only be set when check_compatibility is true
				self.changed = 1
				del ctx.enableSave
			
			# just update that the loading is finished
			self.progressCallback(1.0)
			
			# the progress dialog will disappear
			self.progress = None
			
##				# For the lightweight version we set SMIL files as being "new"
##				if light and mtype == 'application/smil':
##					# XXXX Not sure about this, this may mess up code in read_it
##					self.new_file = 1

		elif mtype == 'application/x-grins-binary-project':
			self.progress = windowinterface.ProgressDialog("Loading")
			self.progressMessage = "Loading GRiNS document..."
			import QuickRead
			self.root = QuickRead.ReadFile(self.filename, progressCallback = (self.progressCallback, 0.5))
			self.progressCallback(1.0)
			if sys.platform == 'wince':
				self.progress.close()
			self.progress = None
		else:
			if sys.platform == 'win32':
				# XXX: experimental code
				lf = filename.lower()
				if lf.find('.asx')>=0:
					self.__import_asx(filename)
					return
			windowinterface.showmessage('%s is a media item.\nCreating new SMIL file around it.'%filename)
			from MediaRead import MediaRead
			self.root = MediaRead(self.filename, mtype, self.printfunc)
			self.new_file = 1

##		t1 = time.time()
##		print 'done in', round(t1-t0, 3), 'sec.'

	def setRoot(self, root):
		self.root = root
		self.context = self.root.GetContext()
		self.context.seteditmgr(self.editmgr)
		self.context.toplevel = self
		self.editmgr.setRoot(root)

	def destroyRoot(self, root):
		# get context before it will destroy
		context = root.GetContext()
		# destroy the 'body' part
		root.Destroy()
		# destroy the layout part
		viewportList = context.getviewports()
		for viewport in viewportList:
			viewport.Destroy()
		# finish some context cleanup
		context.destroy()

	# show the views according to:
	# - the source document contains or not any errors
	# note: if the document contains initialy some errors, all views (except source and errors) are disabled
	# - a list of views to show is specified or not.
	# if a list of view is spefified, the parameter listViewsToShow is a list of view index
	# if no list specified, the default views are showed
	def showviews(self, listViewsToShow=None):
		if self.context.disableviews:
			self.viewsdisabled = 1
		else:
			# if no list specified or previous views was disabled, then show the default views
			if listViewsToShow == None or self.viewsdisabled:
				self.showdefaultviews()
			else:
				for i, geom in listViewsToShow:
					self.views[i].set_geometry(geom)
					self.views[i].show()

			# special case, if all views was previously disabled
			if self.viewsdisabled:
				# if the source view was showed, we have to keep it showed
				if 8 in listViewsToShow:
					if self.sourceview != None and not self.sourceview.is_showing():
						self.sourceview.show()
				# raz the previous views states
				self.viewsdisabled = 0

		# update views according the errors
		self.updateViewsOnErrors()

	# update the views according the errors in the document source		
	def updateViewsOnErrors(self):
		if not self.context.isValidDocument():
			# the document source contains some errors, force the source and error views to show
			if self.sourceview is not None and not self.sourceview.is_showing():
				self.sourceview.show()
			if self.errorsview is not None:
				self.errorsview.show()
				# pop up the errors view
				self.errorsview.pop()
		else:
			# the document doesn't contains any error, force the error view to hide
			if self.errorsview is not None and self.errorsview.is_showing():
				self.errorsview.hide()
			
	def changeRoot(self, root, text=None):
		# raz the focus
		self.editmgr.setglobalfocus([])

		# destroy the views
		showing = []
		for i in range(len(self.views)):
			if self.views[i] is not None and \
					self.views[i].is_showing():
				geom = self.views[i].get_geometry()
				showing.append((i, geom))
		self.destroyviews()
		
		# update the document root			
		self.setRoot(root)			

		# restore the views			
		self.makeviews()
		self.showviews(showing)
		
		# mark the document as changed
		# XXX if the document is restored to a initial state, this flag should be cleared
		self.changed = 1
		
		# re-build the command list. If the document contains some parse errors,
		# we some command are disactivate. In addition, the available views may not
		# be the sames
		self.update_undocommandlist()

	def do_read_it_from_string(self, text):
		import SMILTreeRead

		# init progress bar dialog
		self.progress = windowinterface.ProgressDialog("Reloading")
		self.progressMessage = "Reloading SMIL document from source view..."
		self.progress.set(self.progressMessage)

		try:		
			self.root = SMILTreeRead.ReadString(text, self.filename, self.printfunc, progressCallback = (self.progressCallback, 0.5))
		except (UserCancel, IOError):				
			# the progress dialog will desapear
			self.progress = None
			# re-raise
			raise sys.exc_type

		# just update that the loading is finished
		self.progressCallback(1.0)
		# the progress bar will desapear
		self.progress = None
		
		self.root = self.checkParseErrors(self.root)
		self.setRoot(self.root)

	# this method is called by the parser to print the error messages		
	def printfunc(self, msg):
		# in this version, the error messages aren't printed at this step, but later in order to reduce the dialog box number
		pass
	
	def close_callback(self):
		self.setwaiting()
		self.close()

	def close(self):
		ok = self.close_ok()
		if ok:
			self.saveviewgeometries()
			self.destroy()

	def close_ok(self):
		sourceModified = self.sourceview is not None and self.sourceview.is_changed()

		# if no change, and source not modified, can close
		if not self.changed and not sourceModified:
			return 1
		
		# the things to do depend of the case
		if sourceModified:
			message = 'There are unsaved changes in the source view.\n' + \
				'Discard these changes?'
			ret = windowinterface.GetOKCancel(message, self.window)
			if ret == 0:
				# yes, the user is agree to discard the modifications
				return 1
			else:
				# cancel, do nothing
				return 0

		# the source has been modified			
		message = 'There are unsaved changes in your document.\n' + \
			 'Do you want to save them before closing?'			
		ret = windowinterface.GetYesNoCancel(message, self.window)
		
		if ret == 2:
			# cancel, do nothing
			return 0
		elif ret == 1:
			# no, don't save, and close
			return 1

		# the user wants to save the document before closing
		utype, host, path, params, query, fragment = urlparse(self.filename)
		if self.new_file or (utype and utype != 'file') or (host and host != 'localhost'):
			# new or remote document, save locally
			self.saveas_callback(close = 1)
			return 0
		file = MMurl.url2pathname(path)
		return self.save_to_file(file)

	def help_callback(self, params=None):
		import Help
		Help.showhelpwindow()

	def setwaiting(self):
		windowinterface.setwaiting()

	#
	# EditMgr interface (as dependent client).
	# This is the first registered client; hence its commit routine
	# will be called first, so it can fix the timing for the others.
	# It also flushes the attribute cache maintained by MMAttrdefs.
	#
	def transaction(self, type):
		# Always allow transactions
		return 1

	def commit(self, type):
		# Fix the timing -- views may depend on this.
		MMAttrdefs.flushcache(self.root)
		self.context.changedtimes(self.root)
		self.root.clear_infoicon()
		self.root.ResetPlayability()
		if type != 'preference':
			self.changed = 1
		self.update_undocommandlist()
		self.update_toolbarpulldowns()

	def rollback(self):
		# Nothing has happened.
		pass

	def kill(self):
		print 'TopLevel.kill() should not be called!'

	#
	# Global hyperjump interface
	#
	def jumptoexternal(self, srcanchor, dstanchor, atype, stype=A_SRC_PLAY, dtype=A_DEST_PLAY):
		# XXXX Should check that document isn't active already,
		# XXXX and, if so, should jump that instance of the
		# XXXX document.
		if type(dstanchor) is type(''):
			url, aid = MMurl.splittag(dstanchor)
			url = MMurl.basejoin(self.filename, url)
		else:
			url = self.filename
			for aid, uid in self.root.SMILidmap.items():
				if uid == dstanchor.GetUID():
					break
			else:
				# XXX can't find the SMIL name, guess...
				aid = MMAttrdefs.getattr(dstanchor, 'name')

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
				# or if the external attribute is set,
				# it's handled by an external application
				mtype = urlcache.mimetype(url)
				utype, url2 = MMurl.splittype(url)
				if mtype in ('application/smil',
					     'application/x-grins-project',
					     ) and \
				   not MMAttrdefs.getattr(srcanchor, 'external'):
					# in this case, the document is handled by grins
					top = TopLevel(self.main, url, 0)
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
					'Cannot open: %s\n\n%s.' % (url, msg))
				return 0

		if grinsTarget:
			top.show()
			# update the recent list.
			if self.main != None:
				self.main._update_recent(None)

			node = top.root
			if hasattr(node, 'SMILidmap') and node.SMILidmap.has_key(aid):
				uid = node.SMILidmap[aid]
				node = node.context.mapuid(uid)
			if dtype == A_DEST_PLAY:
				top.player.show()
				top.player.playfromanchor(node)
			elif dtype == A_DEST_PAUSE:
				top.player.show()
				top.player.playfromanchor(node)
				top.player.pause(1)
			else:
				print 'jump to external: invalid destination state'

		if atype == TYPE_JUMP:
			if grinsTarget:
				self.close()
			else:
				self.player.hide()
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
		if self.filename == url:
			return 1
		if MMurl.canonURL(self.filename) == MMurl.canonURL(url):
			return 1
		return 0

	def __import_asx(self, filename):
		windowinterface.showmessage('%s is an ASX file.\nCreating its SMIL representation.'%filename)
		import ASXParser
		strAsxSmil = ASXParser.asx2smil(filename)
		import SMILTreeRead
		self.root = SMILTreeRead.ReadString(strAsxSmil, filename, self.printfunc)

if os.name == 'posix':
	def make_backup_filename(filename):
		return filename + '~'
else:
	def make_backup_filename(filename):
		filename, ext = os.path.splitext(filename)
		return filename + '.BAK' + ext
