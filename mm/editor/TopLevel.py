__version__ = "$Id$"

import os, posixpath
import sys
import string
import windowinterface
import MMAttrdefs, MMurl
from urlparse import urlparse, urlunparse
from MMExc import *
from AnchorDefs import *
from EditMgr import EditMgr
from ViewDialog import ViewDialog
from Hlinks import *
from usercmd import *
import MMmimetypes
import features
import compatibility

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
		self.select_fdlist = []
		self.select_dict = {}
		self._last_timer_id = None
		self.main = main
		self.new_file = new_file
		self._in_prefschanged = 0
		utype, host, path, params, query, fragment = urlparse(url)
		dir, base = posixpath.split(path)
		if (not utype or utype == 'file') and \
		   (not host or host == 'localhost'):
			# local file
			self.dirname = dir
		else:
			# remote file
			self.dirname = ''
		mtype = MMmimetypes.guess_type(base)[0]
		if mtype in ('application/x-grins-project', 'application/smil',
##			     'application/x-grins-cmif',
			     ):
			self.basename = posixpath.splitext(base)[0]
		else:
			self.basename = base
		url = urlunparse((utype, host, path, params, query, None))
		self.filename = url
		self.window = None	# Created in TopLevelDialog.py
##		self.source = None

		# we create only one edit manager by toplevel window.		
		self.editmgr = EditMgr(self)
		self.editmgr.register(self)

		# read the document		
		self.read_it()
		
		self.__checkInitialErrors()

		# when a document with errors, and if the user accept the errors,
		# the views are not relevant in this case. So we set a flag on the context to say
		# the don't show views (except the source view). It's an easy way to remember when you restore (with undo command)
		# the original document
		if not self.context.isValidDocument():
			self.context.disableviews = 1
		
		self.set_commandlist()

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
		if parseErrors != None:
			message = "The source document contains some errors.\nDo you wish to accept GRiNS' automatic fixes?"
			if allowCancel:
				ret = windowinterface.GetYesNoCancel(message, self.window)
			else:
				ret = windowinterface.GetYesNo(message, self.window)
			if ret == 0: # yes
				# accept the errors automatically fixed by GRiNS
				context.setParseErrors(None)
			elif ret == 1: # no
				# default treatement: accept errors and don't allow to edit another view
				pass
			else: # cancel: raise an error: it will be intercepted
				raise MSyntaxError			
		
	# detect the errors/fatal errors
	# if it's a fatal error, then load an empty document to keep GRiNS in a stable state
	def checkParseErrors(self, root):
		parseErrors = root.GetContext().getParseErrors()
		if parseErrors != None:
			if parseErrors.getType() == 'fatal':
				# XXX for now, if there is any fatal error, we load an empty document. In this case, we
				# even be able to edit the source view. 
				import SMILTreeRead
				root = SMILTreeRead.ReadString(EMPTY, self.filename)
				# check that the 'EMPTY' document don't generate as well a fatal error
				# note: it shouldn't happen
				iParseErrors = root.GetContext().getParseErrors()
				if iParseErrors != None and iParseErrors.getType() == 'fatal':
					# re-raise
					raise MSyntaxError

				# if we reload the empty document we have to re-set the previous error
				root.GetContext().setParseErrors(parseErrors)
		return root
		
	def set_commandlist(self):
		self.commandlist = [
			RESTORE(callback = (self.restore_callback, ())),
			CLOSE(callback = (self.close_callback, ())),
			]
			
		if not self.context.disableviews:
			self.commandlist = self.commandlist + [
				PLAY(callback = (self.play_callback, ())),
				PLAYERVIEW(callback = (self.view_callback, (0,))),
				HIERARCHYVIEW(callback = (self.view_callback, (1,))),
				PROPERTIES(callback = (self.prop_callback, ())),

				HIDE_PLAYERVIEW(callback = (self.hide_view_callback, (0,))),
				HIDE_HIERARCHYVIEW(callback = (self.hide_view_callback, (1,))),
				]
		
		if not features.lightweight and not self.context.disableviews:
			self.commandlist = self.commandlist + [
				CHANNELVIEW(callback = (self.view_callback, (2,))),
				LINKVIEW(callback = (self.view_callback, (3,))),
				LAYOUTVIEW(callback = (self.view_callback, (4,))),
				LAYOUTVIEW2(callback = (self.view_callback, (7, ))),
				ASSETSVIEW(callback = (self.view_callback, (9, ))),
				HIDE_LAYOUTVIEW2(callback = (self.hide_view_callback, (7, ))),
				HIDE_CHANNELVIEW(callback = (self.hide_view_callback, (2,))),
				HIDE_LINKVIEW(callback = (self.hide_view_callback, (3,))),
				HIDE_LAYOUTVIEW(callback = (self.hide_view_callback, (4,))),
				HIDE_USERGROUPVIEW(callback = (self.hide_view_callback, (5,))),
				HIDE_ASSETSVIEW(callback = (self.hide_view_callback, (9,))),
				]
			self.__ugroup = [
				USERGROUPVIEW(callback = (self.view_callback, (5,))),
				TRANSITIONVIEW(callback = (self.view_callback, (6, ))),
				HIDE_TRANSITIONVIEW(callback = (self.hide_view_callback, (6, ))),
				]
			#if features.TEMPORAL_VIEW in features.feature_set:
			#	self.commandlist = self.commandlist + [
			#		TEMPORALVIEW(callback = (self.view_callback, (8, ))),
			#		HIDE_TEMPORALVIEW(callback = (self.hide_view_callback, (8,))),
			#		]
			#	
		else:
			self.__ugroup = []

		# the source view command is all the time valid
		self.commandlist.append(SOURCEVIEW(callback = (self.view_callback, (8, ))))
		self.commandlist.append(HIDE_SOURCEVIEW(callback = (self.hide_view_callback, (8, ))))
			
		self.undocommandlist = [
			UNDO(callback = (self.undo_callback, ())),
			REDO(callback = (self.redo_callback, ())),
			]

		self.commandlist_g2 = [] # default, avoid some crashed
		
		if hasattr(self, 'do_edit'):
			self.commandlist.append(EDITSOURCE(callback = (self.edit_callback, ())))
		if self.main.cansave():
			self.commandlist = self.commandlist + [
				SAVE_AS(callback = (self.saveas_callback, ())),
				SAVE(callback = (self.save_callback, ())),
				]
			if self.context.isValidDocument():
				self.commandlist_g2 = self.commandlist + [
					EXPORT_G2(callback = (self.bandwidth_callback, (self.export_G2_callback, ))),
					UPLOAD_G2(callback = (self.bandwidth_callback, (self.upload_G2_callback, ))),
					]
				self.commandlist = self.commandlist + [
					EXPORT_QT(callback = (self.bandwidth_callback, (self.export_QT_callback,))),
					UPLOAD_QT(callback = (self.bandwidth_callback, (self.upload_QT_callback,))),
					]

#				print "TODO: make this version dependant. TopLevel.py:__init__()"
##				self.commandlist.append(EXPORT_WMP(callback = (self.bandwidth_callback, (self.export_WMP_callback,))));
				self.commandlist.append(EXPORT_WMP(callback = (self.export_WMP_callback,())))
				self.commandlist.append(UPLOAD_WMP(callback = (self.bandwidth_callback, (self.upload_WMP_callback,))));
				self.commandlist.append(EXPORT_HTML_TIME(callback = (self.export_HTML_TIME_callback,())))
			
				self.commandlist = self.commandlist + [
						EXPORT_SMIL(callback = (self.bandwidth_callback, (self.export_SMIL_callback,))),
						UPLOAD_SMIL(callback = (self.bandwidth_callback, (self.upload_SMIL_callback,))),
					]								
		import Help
		if hasattr(Help, 'hashelp') and Help.hashelp():
			self.commandlist.append(
				HELP(callback = (self.help_callback, ())))
##		if hasattr(self.root, 'source') and \
##		   hasattr(windowinterface, 'textwindow'):
##			self.commandlist = self.commandlist + [
##				SOURCE(callback = (self.source_callback, ())),
##				HIDE_SOURCE(callback = (self.hide_source_callback, ())),
##				]

		# make the commandlist specific to the plateform
		TopLevelDialog.set_commandlist(self)
			
	def update_undocommandlist(self):
		undocommandlist = []
		if self.editmgr.history:
			undocommandlist = undocommandlist + self.undocommandlist[:1]
		if self.editmgr.future:
			undocommandlist = undocommandlist + self.undocommandlist[1:]
		if self.context.attributes.get('project_boston', 0):
			self.setcommands(self.commandlist + self.__ugroup + undocommandlist)
		else:
			self.setcommands(self.commandlist + self.commandlist_g2 + undocommandlist)
		
	def show(self):
		TopLevelDialog.show(self)
		if self.context.attributes.get('project_boston', 0):
			self.setcommands(self.commandlist + self.__ugroup)
		else:
			self.setcommands(self.commandlist + self.commandlist_g2)

		# This flag allow to know if the current views are disabled.
		# It's use the following raison: if you fix all errors after the initial state, you can easily known that
		# you have to turn on the views
		self.viewsdisabled = 0
		
		self.updateShowingViews()
		
	def showdefaultviews(self):
		import settings
		defaultviews = settings.get('defaultviews')
		if 'hierarchy' in defaultviews and self.hierarchyview is not None:
			self.hierarchyview.show()
		if 'player' in defaultviews and self.player is not None:
			self.player.show()
		if 'channel' in defaultviews and self.channelview is not None:
			self.channelview.show()
		if 'transition' in defaultviews and self.transitionview is not None:
			self.transitionview.show()
		if 'layout' in defaultviews and self.layoutview is not None:
			self.layoutview.show()
		if 'layout2' in defaultviews and self.layoutview2 is not None:
			self.layoutview2.show()
		if 'ugroup' in defaultviews and self.ugroupview is not None:
			self.ugroupview.show()
		if 'link' in defaultviews and self.links is not None:
			self.links.show()
		if 'source' in defaultviews and self.sourceview is not None:
			self.sourceview.show()
		if 'assets' in defaultviews and self.assetsview is not None:
			self.assetsview.show()

	def destroy(self):
		self.set_timer(-1)
		self.hideviews()
		type, data = self.editmgr.getclip()
		if type == 'node' and data is not None:
			self.editmgr.setclip('', None)
			data.Destroy()
		self.editmgr.unregister(self)
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

	def timer_callback(self):
		self._last_timer_id = None
		self.player.timer_callback()

	def set_timer(self, delay):
		if self._last_timer_id is not None:
			windowinterface.canceltimer(self._last_timer_id)
			self._last_timer_id = None
		if delay >= 0:
			self._last_timer_id = windowinterface.settimer(delay,
				  (self.timer_callback, ()))

	#
	# View manipulation.
	#
	def makeviews(self):
		# Reads settings from features.py and loads whichever views are needed..
		self.channelview = None
		self.layoutview = None
		self.ugroupview = None
		self.player = None
		self.hierarchyview = None
		self.links = None
		self.layoutview2 = None
		self.transitionview = None
#		self.temporalview = None
		self.sourceview = None
		self.assetsview = None

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
				except ImportError:
					hasLayoutView2 = 0
					self.layoutview2 = None
				else:
					hasLayoutView2 = 1
					self.layoutview2 = LayoutView2.LayoutView2(self)
			else:
				self.layoutview2 = None

		if features.CHANNEL_VIEW in features.feature_set:
			import ChannelView
			self.channelview = ChannelView.ChannelView(self)

		if features.HYPERLINKS_VIEW in features.feature_set:
			import LinkEdit
			self.links = LinkEdit.LinkEdit(self)

			# Alain's view is used instead of this.
			#import LayoutView
			#self.layoutview = LayoutView.LayoutView(self)

		if features.USER_GROUPS in features.feature_set:
			import UsergroupView
			self.ugroupview = UsergroupView.UsergroupView(self)
			
		if features.LINKEDIT_LIGHT in features.feature_set:
			#I'm not sure what this does.. -mjvdg.
			import LinkEditLight
			self.links = LinkEditLight.LinkEditLight(self)

#		if features.TEMPORAL_VIEW in features.feature_set:
#			import TemporalView
#			self.temporalview = TemporalView.TemporalView(self)

		if features.SOURCE_VIEW in features.feature_set:
			import SourceView
			self.sourceview = SourceView.SourceView(self)

		if features.ASSETS_VIEW in features.feature_set:
			import AssetsView
			self.assetsview = AssetsView.AssetsView(self)

		# Views that are destroyed by restore (currently all)
		# Notice that these must follow a certain order.
		self.views = [self.player, self.hierarchyview,
			      self.channelview, self.links, self.layoutview,
			      self.ugroupview, self.transitionview, self.layoutview2,
			      self.sourceview, self.assetsview
			      ]
#			      self.temporalview]

	def hideviews(self):
		for v in self.views:
			if v is not None:
				v.hide()
##		self.hide_source_callback()

	def destroyviews(self):
		for v in self.views:
			if v is not None:
				v.destroy()

	def checkviews(self):
		pass

#	def open_node_in_tview(self, node):
#		# This causes the temporal view to open the particular node as the root.
#		if self.temporalview:
#			self.temporalview.show()
#			self.temporalview.goto_node(node)
#		else:
#			windowinterface.showmessage('Sorry, but there is no temporal view here.')
	
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

##	def source_callback(self):
##		print "ERROR: You shouldn't be calling TopLevel.sourcecallback!"
##		license = self.main.wanttosave()
##		if not license:
##			windowinterface.showmessage('Cannot obtain a license to save. Operation failed')
##			return
##		evallicense= (license < 0)
##		import SMILTreeWrite
##		self.showsource(SMILTreeWrite.WriteString(self.root, evallicense=evallicense), readonly = 0)

##	def hide_source_callback(self):
##		print "ERROR! You shouldn't be calling TopLevel.soucecallback!"
##		if self.source:
##			self.showsource(None)

	def save_source_callback(self, text):
		# This is a function that is called from the source view when the user decides to save.
		# Compare to edit_finished_callback, which is when a temporary file is used for the sourceview.
		import EditMgr
		if self.editmgr.busy:
			print "Warning! Source view trying to save during an editmgr transaction."
		showing = []
		for i in range(len(self.views)):
			if self.views[i] is not None and \
			   self.views[i].is_showing():
				showing.append(i)
		self.editmgr.unregister(self)
		self.editmgr.destroy() # kills subscribed views
		self.context.seteditmgr(None)
		self.root.Destroy()

		# Now we actually read the text.
		self.do_read_it_from_string(text)

		self.context = self.root.GetContext()
		self.editmgr = EditMgr.EditMgr(self.root)
		self.context.seteditmgr(self.editmgr)
		self.editmgr.register(self)
		self.makeviews()

		self.updateShowingViews(showing)
		
		self.changed = 1
		
	def view_callback(self, viewno):
		self.setwaiting()
		view = self.views[viewno]
		if view is not None:
			view.show()
		else:
			windowinterface.showmessage('View does not exist!', mtype = 'error', parent = self.window)
##		if view.is_showing():
##			view.hide()
##		else:
##			view.show()

	# load a source file without affect the current root
	# return the new root
	def load_source(self, text):		
		# init progress bar dialog
		self.progress = windowinterface.ProgressDialog("Reloading")
		self.progressMessage = "Reloading SMIL document from source view..."
		self.progress.set(self.progressMessage)

		# read the source and update edit manager
		try:
			import SMILTreeRead		
			root = SMILTreeRead.ReadString(text, self.filename, self.printfunc, progressCallback = (self.progressCallback, 0.5))
		except (UserCancel, IOError):				
			# the progress dialog will desapear
			self.progress = None
			# re-raise
			raise sys.exc_type

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

	def bitratecb(self, bitrate):
		import bitrates, settings
		if not self.editmgr.transaction():
			return 0	# indicate failure
		for val, str in bitrates.bitrates:
			if bitrate == str:
				settings.set('system_bitrate', val)
				break
		self.editmgr.commit()
		return 1		# indicate success

	def languagecb(self, language):
		import languages, settings
		if not self.editmgr.transaction():
			return 0	# indicate failure
		for val, str in languages.languages:
			if language == str:
				settings.set('system_language', val)
				break
		self.editmgr.commit()
		return 1		# indicate success

	def save_callback(self):
		if self.new_file:
			self.saveas_callback()
			return
		utype, host, path, params, query, fragment = urlparse(self.filename)
		if (utype and utype != 'file') or (host and host != 'localhost'):
			windowinterface.showmessage('Cannot save to remote URL',
						    mtype = 'warning')
			return
		file = MMurl.url2pathname(path)
		self.setwaiting()
		ok = self.save_to_file(file)

	def saveas_okcallback(self, filename):
		if not filename:
			return 'no file specified'
		self.setwaiting()
		if self.save_to_file(filename):
			self.filename = MMurl.pathname2url(filename)
##			self.context.setbaseurl(self.filename)
			self.fixtitle()
		else:
			return 1

	def saveas_callback(self):
		cwd = self.dirname
		if cwd:
			cwd = MMurl.url2pathname(cwd)
			if not os.path.isabs(cwd):
				cwd = os.path.join(os.getcwd(), cwd)
		else:
			cwd = os.getcwd()
		filetypes = ['application/x-grins-project', 'application/smil']
##		import settings
##		if settings.get('cmif'):
##			filetypes.append('application/x-grins-cmif')
		dftfilename = ''
		if self.filename:
			utype, host, path, params, query, fragment = urlparse(self.filename)
			dftfilename = os.path.split(MMurl.url2pathname(path))[-1]
		windowinterface.FileDialog('Save SMIL file:', cwd, filetypes,
					   dftfilename, self.saveas_okcallback, None)

	def export_okcallback(self, filename):
		exporttype = self.exporttype
			
		if not filename:
			return 'no file specified'
		self.setwaiting()
		license = self.main.wanttosave()
		if not license:
			windowinterface.showmessage('Cannot obtain a license to save. Operation failed')
			return
		evallicense= (license < 0)
		if not self.save_to_file(filename, exporting = 1):
			return		# Error, don't save HTML file
		if exporttype == compatibility.SMIL10:
			return		# don't create HTML file for SMIL 1.0 export
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

	def bandwidth_callback(self, do_export_callback):
		# Calculates the bandwidth for ...something? Uses a dialog? Unsure -mjvdg		
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
		bandwidth, prerolltime, delaycount, errorseconds, errorcount = \
			BandwidthCompute.compute_bandwidth(self.root)
		dialog.setinfo(prerolltime, errorseconds, delaycount, errorcount)
		dialog.done(do_export_callback, cancancel=1)

	def export_G2_callback(self):
		self.export(compatibility.G2)
		
	def export_QT_callback(self):
		self.export(compatibility.QT)

	def export_SMIL_callback(self):
		self.export(compatibility.SMIL10)

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
		ask = self.new_file

		# TODO: this also has to handle WMP -mjvdg.

		if not ask:
			if MMmimetypes.guess_type(self.filename)[0] != 'application/x-grins-project':
				# We don't have a project file name. Ask for filename.
				ask = 1
			else:
				utype, host, path, params, query, fragment = urlparse(self.filename)
				if (utype and utype != 'file') or (host and host != 'localhost'):
					# The project file is remote. Ask for filename.
					ask = 1
				else:
					file = MMurl.url2pathname(path)
					base = os.path.splitext(file)[0]
					file = base + MMmimetypes.guess_extension('application/smil')
					self.setwaiting()
					self.export_okcallback(file)
					return 
		cwd = self.dirname
		if cwd:
			cwd = MMurl.url2pathname(cwd)
			if not os.path.isabs(cwd):
				cwd = os.path.join(os.getcwd(), cwd)
		else:
			cwd = os.getcwd()
		windowinterface.FileDialog('Publish SMIL file:', cwd, 'application/smil',
					   '', self.export_okcallback, None)
	   
	def upload_G2_callback(self):
		self.upload(compatibility.G2)
		
	def upload_QT_callback(self):
		self.upload(compatibility.QT)

	def upload_SMIL_callback(self):
		self.upload(compatibility.SMIL10)

	def upload_WMP_callback(self):
		windowinterface.showmessage("Please purchase the full version of GRiNS today!");
		self.upload(compatibility.WMP);
		return;

	def upload(self, exporttype):
		self.exporttype = exporttype
		# TODO: this also has to handle WMP.
		
		# XXXX The filename business confuses project file name and resulting SMIL file
		# XXXX name. To be fixed.
		#
		# XXXX The multi-stage password asking code here is ugly.
		if not self.filename:
			windowinterface.showmessage('Please save your work first')
			return
		have_web_page = (features.compatibility in (compatibility.G2, compatibility.QT))
		filename, smilurl, self.w_ftpinfo, self.m_ftpinfo = self.get_upload_info()
			
		missing = ''
		attr = None
		attrs = self.context.attributes
		if have_web_page:
			if not self.w_ftpinfo[0] or not self.m_ftpinfo[0]:
				attr = 'project_ftp_host'
				missing = '\n- webserver and mediaserver FTP info'
			if not smilurl:
				if not attr: attr = 'project_smil_url'
				missing = missing + '\n- Mediaserver SMILfile URL'
			if not attrs.has_key('project_html_page') or not attrs['project_html_page']:
				if features.lightweight:
					attrs['project_html_page'] = 'external_player.html'
				else:
					if not attr: attr = 'project_html_page'
					missing = missing + '\n- HTML Template'
		else:
			# We only have to check mediaserver params (we don't generate a webpage)
			# For ease of coding we copy the m_ftpinfo to w_ftpinfo, and we then
			# just skip generating/uploading the HTML later
			self.w_ftpinfo = self.m_ftpinfo
			if not self.m_ftpinfo[0]:
				attr = 'project_ftp_host_media'
				missing = '\n- Mediaserver FTP info'
		if missing:
			if windowinterface.showquestion('Please set these parameters then try again:'+missing):
				self.prop_callback(attr)
			return
		if have_web_page:
			# Do a sanity check on the SMILfile URL
			fn = MMurl.url2pathname(string.split(smilurl, '/')[-1])
			if os.path.split(filename)[1] != os.path.split(fn)[1]:
				# The SMIL upload filename and URL don't match. Warn.
				if not windowinterface.showquestion('Warning: Mediaserver SMIL URL appears incorrect:\n'+smilurl):
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
		filename, smilurl, d1, d2  = self.get_upload_info()
		self.save_to_ftp(filename, smilurl, self.w_ftpinfo, self.m_ftpinfo)
		del self.w_ftpinfo
		del self.m_ftpinfo
		
	def get_upload_info(self, w_passwd='', m_passwd=''):
		attrs = self.context.attributes
		have_web_page = (self.exporttype in (compatibility.G2, compatibility.QT))

		# Website FTP parameters
		w_hostname = ''
		w_username = ''
		w_dirname = ''
		if have_web_page:
			if attrs.has_key('project_ftp_host'):
				w_hostname = attrs['project_ftp_host']
			if attrs.has_key('project_ftp_user'):
				w_username = attrs['project_ftp_user']
			if attrs.has_key('project_ftp_dir'):
				w_dirname = attrs['project_ftp_dir']

		# Mediasite FTP params (default to same as website)
		m_hostname = ''
		m_username = ''
		m_dirname = ''
		if attrs.has_key('project_ftp_host_media'):
			m_hostname = attrs['project_ftp_host_media']
		if attrs.has_key('project_ftp_user_media'):
			m_username = attrs['project_ftp_user_media']
		if attrs.has_key('project_ftp_dir_media'):
			m_dirname = attrs['project_ftp_dir_media']
		if not m_hostname:
			m_hostname = w_hostname
		if not m_username:
			m_username = w_username
		if not m_dirname:
			m_dirname = w_dirname
			
		# Filename for SMIL file on media site
		# XXXX This may be wrong, because it uses the "project" filename
		utype, host, path, params, query, fragment = urlparse(self.filename)
		dir, filename = posixpath.split(path)
		filename = posixpath.splitext(filename)[0] + \
			   MMmimetypes.guess_extension('application/smil')
		
		# URL of the SMIL file as it appears on the net
		if have_web_page and attrs.has_key('project_smil_url'):
			smilurl = attrs['project_smil_url']
		else:
			smilurl = ''

		return (filename, smilurl,
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
		import EditMgr, os
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
				showing.append(i)
#		self.editmgr.unregister(self)
#		self.editmgr.destroy() # kills subscribed views
#		self.context.seteditmgr(None)
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
#		self.editmgr = EditMgr.EditMgr(self.root)
#		self.context.seteditmgr(self.editmgr)
#		self.editmgr.register(self)
		self.makeviews()

		self.updateShowingViews(showing)

		self.changed = 1

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
		mtype = MMmimetypes.guess_type(base)[0]
		if mtype in ('application/x-grins-project', 'application/smil',
##			     'application/x-grins-cmif',
			     ):
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
		type, data = self.root.context.editmgr.getclip()
		if type == 'node' and data is not None:
			roots.append(data)
		self.context.sanitize_hyperlinks(roots)
		# Get all windows to save their current geometry.
		for v in self.views:
			if v is not None:
				v.get_geometry()
				v.save_geometry()
		

	def save_to_file(self, filename, exporting = 0):
		license = self.main.wanttosave()
		if not license:
			windowinterface.showmessage('Cannot obtain a license to save. Operation failed')
			return 0
		evallicense= (license < 0)
		url = MMurl.pathname2url(filename)
		mimetype = MMmimetypes.guess_type(url)[0]
		if exporting and mimetype != 'application/smil':
			windowinterface.showmessage('Publish to SMIL (*.smi or *.smil) files only')
			return
##		if mimetype == 'application/x-grins-cmif':
##			if features.lightweight:
##				windowinterface.showmessage('cannot write CMIF files in this version', mtype = 'error')
##				return 0
		if mimetype == 'application/smil':
			if not exporting:
				answer = windowinterface.GetOKCancel('You will lose GRiNS specific information by saving your project as SMIL.')
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
##		print 'saving to', filename, '...'
		try:
##			if mimetype == 'application/x-grins-cmif':
##				import MMWrite
##				MMWrite.WriteFile(self.root, filename, evallicense=evallicense)
##			else:
				if compatibility.QT == features.compatibility:
					cleanSMIL = 0
					if mimetype == 'application/smil':
						grinsExt = 0
					else:
						grinsExt = 1
				else:
					cleanSMIL = (mimetype == 'application/smil')					
					grinsExt = not cleanSMIL
					
				import SMILTreeWrite
				if exporting:
					# XXX enabling this currently crashes the application on Windows during video conversion
					progress = windowinterface.ProgressDialog("Publishing", self.cancel_upload)
					progress.set('Publishing document...')
					progress = progress.set
				else:
					progress = None
				SMILTreeWrite.WriteFile(self.root, filename,
							cleanSMIL = cleanSMIL,
							grinsExt = grinsExt,
							copyFiles = exporting,
							evallicense=evallicense,
							progress = progress,
							convertURLs = 1,
							convertfiles = exporting and self.exporttype != compatibility.SMIL10)
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
##		print 'done saving.'
		if sys.platform == 'mac':
			import macostools
			macostools.touched(filename)
		if not exporting:
			self.main._update_recent(MMurl.pathname2url(filename))
			self.changed = 0
			self.new_file = 0
		if self.context.attributes.get('project_boston', 0):
			self.setcommands(self.commandlist + self.__ugroup)
		else:
			self.setcommands(self.commandlist + self.commandlist_g2)
		return 1
		
	def save_to_ftp(self, filename, smilurl, w_ftpparams, m_ftpparams):
		license = self.main.wanttosave()
		if not license:
			windowinterface.showmessage('Cannot obtain a license to save. Operation failed')
			return 0
		evallicense= (license < 0)
		self.pre_save()
		have_web_page = (self.exporttype in (compatibility.G2, compatibility.QT))
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
			SMILTreeWrite.WriteFTP(self.root, filename, m_ftpparams,
						cleanSMIL = 1,
						copyFiles = 1,
						evallicense=evallicense,
						progress=progress.set)
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
		if self.context.attributes.get('project_boston', 0):
			self.setcommands(self.commandlist + self.__ugroup)
		else:
			self.setcommands(self.commandlist + self.commandlist_g2)
		return 1
		
	def cancel_upload(self):
		raise KeyboardInterrupt

	def export_to_html_time(self, filename):
		license = self.main.wanttosave()
		if not license:
			windowinterface.showmessage('Cannot obtain a license to save. Operation failed')
			return 0
		evallicense= (license < 0)
		url = MMurl.pathname2url(filename)
		mimetype = MMmimetypes.guess_type(url)[0]
		if mimetype != 'text/html':
			windowinterface.showmessage('Publish to HTML (*.htm or *.html) files only')
			return
		self.pre_save()
		try:
			progress = windowinterface.ProgressDialog("Publishing", self.cancel_upload)
			progress.set('Publishing document...')
			progress = progress.set
			import SMILTreeWriteHtmlTime
			SMILTreeWriteHtmlTime.WriteFileAsHtmlTime(self.root, filename,
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
#		if not self.editmgr.transaction():
#			return
		self.setwaiting()
		# keep the showing state of all current views
		showing = []
		for i in range(len(self.views)):
			if self.views[i] is not None and \
			   self.views[i].is_showing():
				showing.append(i)
#		self.editmgr.rollback()
		# cleanup
		self.editmgr.unregister(self)
		self.editmgr.destroy() # kills subscribed views
		self.context.seteditmgr(None)
		self.destroyRoot(self.root)

		# editmgr have to be re-created. 		
		self.editmgr = EditMgr(self)
		self.editmgr.register(self)

		# read the document		
		self.read_it()

		# check initial errors, and don't allow cancel
		self.__checkInitialErrors(0)

		if not self.context.isValidDocument():
			self.context.disableviews = 1
			
		# update command list, re-make the views, and show the views prviously showed		
		self.set_commandlist()
		
		# update the undo/redo 
		self.update_undocommandlist()
		
		self.makeviews()

		self.updateShowingViews(showing)

	def read_it(self):
		self.changed = 0
		if self.new_file:
			if type(self.new_file) == type(''):
				self.do_read_it(self.new_file)
			else:
				import SMILTreeRead
				self.root = SMILTreeRead.ReadString(EMPTY, self.filename)
		else:
			self.do_read_it(self.filename)
		self.root = self.checkParseErrors(self.root)
		self.setRoot(self.root)
		if self.new_file:
			self.context.baseurl = ''
			if type(self.new_file) == type(''):
				self.context.template = self.new_file

	def progressCallback(self, pValue):
		self.progress.set(self.progressMessage, None, None, pValue*100, 100)
		
	def do_read_it(self, filename):
##		import time
##		print 'parsing', filename, '...'
##		t0 = time.time()
		mtype = MMmimetypes.guess_type(filename)[0]
		if mtype == None and sys.platform == 'mac':
			# On the mac we do something extra: for local files we attempt to
			# get creator and type, and if they are us we assume we're looking
			# at a SMIL file.
			import MacOS
			utype, host, path, params, query, fragment = urlparse(filename)
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
			
			check_compatibility = mtype == 'application/x-grins-project'
			try:
				self.root = SMILTreeRead.ReadFile(filename, self.printfunc, self.new_file, check_compatibility, \
												  progressCallback=(self.progressCallback, 0.5))
			except (UserCancel, IOError):				
				# the progress dialog will desapear
				self.progress = None
				# re-raise
				raise sys.exc_type
			
			# just update that the loading is finished
			self.progressCallback(1.0)
			
			# the progress dialog will desapear
			self.progress = None
			
##				# For the lightweight version we set SMIL files as being "new"
##				if light and mtype == 'application/smil':
##					# XXXX Not sure about this, this may mess up code in read_it
##					self.new_file = 1

##		elif mtype == 'application/x-grins-cmif':
##			if features.lightweight:
##				windowinterface.showmessage('cannot read CMIF files in this version', mtype = 'error')
##				raise Error, filename
##			import MMRead
##			self.root = MMRead.ReadFile(filename)
		else:
			if sys.platform == 'win32':
				# XXX: experimental code
				lf = filename.lower()
				if lf.find('.asx')>=0:
					self.__import_asx(filename)
					return
			windowinterface.showmessage('%s is a media item.\nCreating new SMIL file around it.'%filename)
			import SMILTreeRead
			if mtype is None or \
			   (mtype[:6] != 'audio/' and \
			    mtype[:6] != 'video/'):
				dur = ' dur="indefinite"'
			else:
				dur = ''
			self.new_file = 1
			self.root = SMILTreeRead.ReadString('''\
<smil>
  <body>
    <ref%s src="%s"/>
  </body>
</smil>
''' % (dur, filename), filename, self.printfunc)

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

	def updateShowingViews(self, listViewsToShow=None):
		forceSourceView = 0
		if self.context.disableviews:
			self.viewsdisabled = 1
			forceSourceView = 1
		else:
			# if no list specified or previous views was disabled, then show default views
			if listViewsToShow == None or self.viewsdisabled:
				self.showdefaultviews()
			else:
				for i in listViewsToShow:
					self.views[i].show()

			if self.viewsdisabled:
				# if the source view was showed, we have to keep it showed
				if 8 in listViewsToShow:
					forceSourceView = 1
				# raz the previous views states
				self.viewsdisabled = 0

		# if the sourceview is requiered or the document is not valid (parse error),
		# show in addition the source view
		if forceSourceView or not self.context.isValidDocument():
			if self.sourceview != None and not self.sourceview.is_showing():
				self.sourceview.show()		
					
	def changeRoot(self, root, text=None):
		# raz the focus
		self.editmgr.setglobalfocus(None, None)

		# destroy the views
		showing = []
		for i in range(len(self.views)):
			if self.views[i] is not None and \
				self.views[i].is_showing():
				showing.append(i)
		self.destroyviews()
		
		# update the document root			
		self.setRoot(root)			

		# restore the views			
		self.makeviews()
		self.updateShowingViews(showing)
		
		# re-build the command list. If the document contains some parse errors,
		# we some command are disactivate. In addition, the available views may not
		# be the sames
		self.set_commandlist()
		
		# update the undo/redo 
		self.update_undocommandlist()

		# mark the document as changed
		# XXX if the document is restored to a initial state, this flag should be cleared
		self.changed = 1
		
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
		
	def printfunc(self, msg):
		windowinterface.showmessage('while reading %s\n\n' % self.filename + msg)

	def close_callback(self):
		self.setwaiting()
##		if self.source and not self.source.is_closed():
##			self.source.close()
##		self.source = None
		self.close()

	def close(self):
		ok = self.close_ok()
		if ok:
			self.destroy()

	def close_ok(self):
		sourceModified = self.sourceview != None and self.sourceview.is_changed()

		# if no changement, and source not modified, can close
		if not self.changed and not sourceModified:
			return 1
		
		# the things to do depend of the case
		if sourceModified:
			message = 'Are you sure you want to close the document?\n'+\
					'(This will destroy the changes you have made)\n' +\
					'Click OK to close, Cancel to keep your changes.'
			ret = windowinterface.GetOKCancel(message, self.window)
			if ret == 0:
				# yes, the user is agree to discard the modifications
				return 1
			else:
				# cancel, do nothing
				return 0

		# the source has been modified			
		message = 'You haven\'t saved your changes yet.\n' + \
			 'Do you want to save them before closing?'			
		ret = windowinterface.GetYesNoCancel(message, self.window)
		
		if ret == 2:
			# cancel, do nothing
			return 0
		elif ret == 1:
			# no, don't save, and close
			return 1

		# the user want to save the document, before to close
		utype, host, path, params, query, fragment = urlparse(self.filename)
		if (utype and utype != 'file') or (host and host != 'localhost'):
			windowinterface.showmessage('Cannot save to URL',
						    mtype = 'warning')
			return 0
		file = MMurl.url2pathname(path)
		# XXXX This is wrong, we should ask where to save if self.new_file is set.
		# But we can't do that because we have to synchronously return...
		return self.save_to_file(file)

	def help_callback(self, params=None):
		import Help
		Help.showhelpwindow()

	def setwaiting(self):
		windowinterface.setwaiting()
		pass

	def prefschanged(self):
		# HACK: we don't want to set the file changed bit (in the
		# commit call below)
		self._in_prefschanged = 1
		if not self.editmgr.transaction():
			return
		self.editmgr.commit()
		self._in_prefschanged = 0
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
		if not self._in_prefschanged:
			self.changed = 1
##		if self.source:
##			# reshow source
##			license = self.main.wanttosave()
##			if not license:
##				windowinterface.showmessage('Cannot obtain a license to save. Operation failed')
##				return
##			evallicense= (license < 0)
##			import SMILTreeWrite
##			self.showsource(SMILTreeWrite.WriteString(self.root, evallicense=evallicense), optional=1)
		self.update_undocommandlist()

	def rollback(self):
		# Nothing has happened.
		pass

	def kill(self):
		print 'TopLevel.kill() should not be called!'

	#
	# Global hyperjump interface
	#
	def jumptoexternal(self, anchor, atype, stype=A_SRC_PLAY, dtype=A_DEST_PLAY):
		# XXXX Should check that document isn't active already,
		# XXXX and, if so, should jump that instance of the
		# XXXX document.
		import MMurl
		url, aid = MMurl.splittag(anchor)
			
		# by default, the document target will be handled by GRiNS
		# note: this varib allow to manage correctly the sourcePlaystate attribute
		# as well, even if the target document is not handled by GRiNS
		grinsTarget = 1
		
		url = MMurl.basejoin(self.filename, url)
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
##					     'application/x-grins-cmif',
					     ):
					# in this case, the document is handle by grins
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

	def _getlocalexternalanchors(self):
		fn = self.filename
		if not '/' in fn:
			fn = './' + fn
		rv = []
		for a in MMAttrdefs.getattr(self.root, 'anchorlist'):
			rv.append((fn, a.aid))
		return rv

	def getallexternalanchors(self):
		rv = []
		for top in self.main.tops:
			if top is not self:
				rv = rv + top._getlocalexternalanchors()
		return rv

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
		return filename + '.BAK'
