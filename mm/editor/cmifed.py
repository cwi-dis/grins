__version__ = "$Id$"

# Main program for the CMIF editor.

import sys
import os
import features

# The next line enables/disables the CORBA interface to GRiNS

ENABLE_FNORB_SUPPORT = 0
NUM_RECENT_FILES = 10

import getopt

def usage(msg):
	sys.stdout = sys.stderr
	print msg
	print 'usage: cmifed [-qpsnTHPSL] [-h helpdir] file ...'
	print '-q         : quiet (don\'t print anything to stdout)'
	print '-p         : start playing right away'
	print '-j name    : start playing at given global anchor'
	print '-s         : report statistics (guru only)'
	print '-n         : no pre-arming (guru only)'
	print '-C         : open Channel view right away'
	print '-H         : open Structure view right away'
	print '-P         : open Player window right away'
##	print '-S         : open Style sheet window right away'
	print '-L         : open Hyperlinks window right away'
	print '-h helpdir : specify help directory'
	print 'file ...   : one or more CMIF files'
	sys.exit(2)

from MainDialog import MainDialog
from usercmd import *

class Main(MainDialog):
	def __init__(self, opts, files):
		import windowinterface
		import license
		import features
		if hasattr(features, 'expiry_date') and features.expiry_date:
			import time
			import version
			tm = time.localtime(time.time())
			yymmdd = tm[:3]
			if yymmdd > features.expiry_date:
				rv = windowinterface.GetOKCancel(
				   "This beta copy of GRiNS has expired.\n\n"
				   "Do you want to check www.oratrix.com for a newer version?")
				if rv == 0:
					url = 'http://www.oratrix.com/indir/%s/update.html'%version.shortversion
					windowinterface.htmlwindow(url)
				sys.exit(0)
		self.tmpopts = opts
		self.tmpfiles = files
		self.tmplicensedialog = license.WaitLicense(self.do_init,
					   features.license_features_needed)
		self.recent_file_list = [] # This is the list of recently opened files.

	def do_init(self, license):
		opts, files = self.tmpopts, self.tmpfiles
		del self.tmpopts
		del self.tmpfiles
##		del self.tmplicensedialog
		import MMurl
		import windowinterface
		if features.lightweight and len(files) > 1:
			windowinterface.showmessage('Cannot open multiple files in this version')
			files = files[:1]
		self._license = license
##		if not self._license.have('save'):
##			windowinterface.showmessage(
##				'This is a demo version.\n'+
##				'You will not be able to save your changes.',
##				title='CMIFed license')
		self._tracing = 0
		self.tops = []
		self._mm_callbacks = {}
		self.last_location = ''
		self._untitled_counter = 1
		self.template_info = None
		try:
			import mm, posix, fcntl, FCNTL
		except ImportError:
			pass
		else:
			pipe_r, pipe_w = posix.pipe()
			mm.setsyncfd(pipe_w)
			self._mmfd = pipe_r
			windowinterface.select_setcallback(pipe_r,
						self._mmcallback,
						(posix.read, fcntl.fcntl, FCNTL))
		self.commandlist = [
			EXIT(callback = (self.close_callback, ())),
			NEW_DOCUMENT(callback = (self.new_callback, ())),
			OPEN(callback = (self.open_callback, ())),
			OPENFILE(callback = (self.openfile_callback, ())),
			OPEN_RECENT(callback = self.open_recent_callback),	# Dynamic cascade
			PREFERENCES(callback=(self.preferences_callback, ())),
			CHECKVERSION(callback=(self.checkversion_callback, ())),
			]
		import Help
		if hasattr(Help, 'hashelp') and Help.hashelp():
			self.commandlist.append(
				HELP(callback = (self.help_callback, ())))
		import settings
		if settings.get('debug'):
			self.commandlist = self.commandlist + [
				TRACE(callback = (self.trace_callback, ())),
				DEBUG(callback = (self.debug_callback, ())),
				CRASH(callback = (self.crash_callback, ())),
				]
		MainDialog.__init__(self, 'CMIFed', (not not files))

		for file in files:
			self.openURL_callback(MMurl.guessurl(file))
		self._update_recent(None)

		if ENABLE_FNORB_SUPPORT:
			import CORBA.services
			self.corba_services = CORBA.services.services(sys.argv)
			
	def collect_template_info(self):
		import SMILTreeRead
		import MMmimetypes
		import MMurl
		self.templatedir = findfile('Templates')
		if not os.path.exists(self.templatedir):
			self.template_info = ()
			return
		names = []
		descriptions = []
		files = os.listdir(self.templatedir)
		files.sort()
		for file in files:
			url = MMurl.pathname2url(file)
			pathname = os.path.join(self.templatedir, file)
			if not os.path.isfile(pathname):
				continue
			if MMmimetypes.guess_type(url)[0] != 'application/x-grins-project':
				continue
			pathname = os.path.join(self.templatedir, file)
			try:
				attrs = SMILTreeRead.ReadMetaData(pathname)
			except IOError:
				windowinterface.showmessage('Invalid template: %s'%file)
			name = attrs.get('template_name', file)
			description = attrs.get('template_description', '')
			image = attrs.get('template_snapshot', None)
			if image:
				image = os.path.join(self.templatedir, image)
			names.append(name)
			descriptions.append((description, image, pathname))
		self.template_info = (names, descriptions)

	def never_again(self):
		# Called when the user selects the "don't show again" in the initial dialog
		import settings
		settings.set('initial_dialog', 0)
		settings.save()

	def new_callback(self):
		import TopLevel
		import windowinterface
		
		if not self.canopennewtop():
			return
		if self.template_info is None:
			self.collect_template_info()
		if self.template_info:
			names, descriptions = self.template_info
			windowinterface.TemplateDialog(names, descriptions,self._new_ok_callback, parent=self.getparentwindow())
		else:
			windowinterface.showmessage("No Templates found, creating empty document")
			top = TopLevel.TopLevel(self, self.getnewdocumentname(mimetype="application/x-grins-project"), 1)
			self.new_top(top)
	
	def help_callback(self, params=None):
		import Help
		Help.showhelpwindow()

	def _new_ok_callback(self, info):
		if not info:
			return
		if len(info) == 3:
			d1, d2, filename = info
			htmltemplate = None
		else:
			d1, d2, filename, htmltemplate = info
		import windowinterface
		windowinterface.setwaiting()
		import TopLevel
		import MMurl
		from MMExc import MSyntaxError, UserCancel
		template_url = MMurl.pathname2url(filename)
		try:
			top = TopLevel.TopLevel(self, self.getnewdocumentname(filename), template_url)
		except IOError:
			import windowinterface
			windowinterface.showmessage('error opening document %s' % filename)
		except MSyntaxError:
			import windowinterface
			windowinterface.showmessage('parsing document %s failed' % filename)
		except UserCancel:
			return
		except TopLevel.Error:
			return
		self.new_top(top)
		if htmltemplate:
			top.context.attributes['project_html_page'] = htmltemplate
		
	def getnewdocumentname(self, templatename=None, mimetype=None):
		name = 'Untitled%d'%self._untitled_counter
		self._untitled_counter = self._untitled_counter + 1
		if mimetype:
			import MMmimetypes
			ext = MMmimetypes.guess_extension(mimetype)
		else:
			dummy, ext = os.path.splitext(templatename)
		return name + ext
		
	def canopennewtop(self):
		# Return true if a new top can be opened (only one top in the light version)
		if not features.lightweight:
			return 1
		for top in self.tops:
			top.close()
		if self.tops:
			return 0
		return 1

	def openURL_callback(self, url):
		if not self.canopennewtop():
			return
		import windowinterface
		self.last_location = url
		windowinterface.setwaiting()
		from MMExc import MSyntaxError, UserCancel
		import TopLevel
		for top in self.tops:
			if top.is_document(url):
				windowinterface.showmessage("%s is already open"%url)
				return
		try:
			top = TopLevel.TopLevel(self, url, 0)
		except IOError:
			import windowinterface
			windowinterface.showmessage('error opening document %s' % url)
		except MSyntaxError:
			import windowinterface
			windowinterface.showmessage('parsing document %s failed' % url)
		except UserCancel:
			return
		except TopLevel.Error:
			return
		else:
			self.new_top(top)
			self._update_recent(url)
			
	def open_recent_callback(self, url):
		if not self.canopennewtop():
			return
		self.openURL_callback(url)
		
	def _update_recent(self, url):
		if url:
			self.add_recent_file(url)
		doclist = self.get_recent_files()
		self.set_recent_list(doclist)

	def get_recent_files(self):
		if not hasattr(self, 'set_recent_list'):
			return
		import settings
		import posixpath
		recent = settings.get('recent_documents')
		doclist = []
		for url in recent:
			base = posixpath.basename(url)
			doclist.append( (base, (url,)))
		return doclist

	def add_recent_file(self, url):
		# Add url to the top of the recent file list.
		assert url
		import settings
		recent = settings.get('recent_documents')
		if url in recent:
			recent.remove(url)
		recent.insert(0, url)
		if len(recent) > NUM_RECENT_FILES:
			recent = recent[:NUM_RECENT_FILES]
		settings.set('recent_documents', recent)
		settings.save()

	def close_callback(self, exitcallback=None):
		import windowinterface
		windowinterface.setwaiting()
		self.do_exit(exitcallback)

	def crash_callback(self):
		raise 'Crash requested by user'
		
	def debug_callback(self):
		import pdb
		pdb.set_trace()

	def trace_callback(self):
		import trace
		if self._tracing:
			trace.unset_trace()
			self._tracing = 0
		else:
			self._tracing = 1
			trace.set_trace()
			
	def preferences_callback(self):
		import AttrEdit
		AttrEdit.showpreferenceattreditor(self.prefschanged)

	def prefschanged(self):
		import settings
		for top in self.tops:
			top.prefschanged()
		settings.save()
		
	def checkversion_callback(self):
		import MMurl
		import version
		import windowinterface
		import settings
		import string
		url = 'http://www.oratrix.com/indir/%s/updatecheck.txt'%version.shortversion
		try:
			fp = MMurl.urlopen(url)
			data = fp.read()
			fp.close()
		except:
			windowinterface.showmessage('Unable to check for upgrade. You can try again later, or visit www.oratrix.com with your webbrowser.')
			return
		if not data:
			windowinterface.showmessage('You are running the latest version of the software')
			return
		cancel = windowinterface.GetOKCancel('There appears to be a newer version!\nDo you want to hear more?')
		if cancel:
			return
		data = string.strip(data)
		# Pass the version and the second item of the license along.
		id = string.split(settings.get('license'), '-')[1]
		url = '%s?version=%s&id=%s'%(data, version.shortversion, id)
		windowinterface.htmlwindow(url)

	def new_top(self, top):
		top.show()
		top.checkviews()
		self.tops.append(top)

	def do_exit(self, exitcallback=None):
		# XXXX This is pretty expensive (and useless) if AttrEdit hasn't been used...
		import AttrEdit
		AttrEdit.closepreferenceattreditor()
		ok = 1
		for top in self.tops[:]:
			top.close()
		if self.tops:
			return
		if sys.platform == 'mac':
			import MacOS
			MacOS.OutputSeen()
		if exitcallback:
			rtn, arg = exitcallback
			apply(rtn, arg)
		else:
			raise SystemExit, 0
		
	def run(self):
		import windowinterface
		windowinterface.mainloop()

	def setmmcallback(self, dev, callback):
		if callback:
			self._mm_callbacks[dev] = callback
		elif self._mm_callbacks.has_key(dev):
			del self._mm_callbacks[dev]

	def _mmcallback(self, read, fcntl, FCNTL):
		# set in non-blocking mode
		dummy = fcntl(self._mmfd, FCNTL.F_SETFL, FCNTL.O_NDELAY)
		# read a byte
		devval = read(self._mmfd, 1)
		# set in blocking mode
		dummy = fcntl(self._mmfd, FCNTL.F_SETFL, 0)
		# return if nothing read
		if not devval:
			return
		devval = ord(devval)
		dev, val = devval >> 2, devval & 3
		if self._mm_callbacks.has_key(dev):
			func = self._mm_callbacks[dev]
			func(val)
		else:
			print 'Warning: unknown device in mmcallback'

	def save(self):
		# this is a debug method.  it can be used after a
		# crash to save the documents being edited.
		for top in self.tops:
			nf = top.new_file
			top.new_file = 0
			ok = top.save_callback()
			top.new_file = nf

	def cansave(self):
		return 1
	
	def wanttosave(self):
##		import license
##		import windowinterface
##		try:
##			features = self._license.need('save')
##		except license.Error, arg:
##			print "No license:", arg
##			return 0
		if self._license.is_evaluation_license():
			return -1
		return 1

def main():
	try:
		opts, files = getopt.getopt(sys.argv[1:], 'qsnh:')
	except getopt.error, msg:
		usage(msg)

	if os.environ.has_key('PRELOADDOC') and not files:
		files.append(os.environ['PRELOADDOC'])

	if sys.argv[0] and sys.argv[0][0] == '-':
		sys.argv[0] = 'cmifed'
	try:
		import splash
	except ImportError:
		splash = None
	else:
		from version import version
		splash.splash(version = 'GRiNS ' + version)

	import settings
	kbd_int = KeyboardInterrupt
	if ('-q', '') in opts:
		sys.stdout = open('/dev/null', 'w')
	elif settings.get('debug'):
		try:
			import signal, pdb
		except ImportError:
			pass
		else:
			signal.signal(signal.SIGINT,
				      lambda s, f, pdb=pdb: pdb.set_trace())
			kbd_int = 'dummy value to prevent interrupts to be caught'

## 	for fn in files:
## 		try:
## 			# Make sure the files exist first...
## 			f = open(fn, 'r')
## 			f.close()
## 		except IOError, msg:
## 			import types
## 			if type(msg) is types.InstanceType:
## 				msg = msg.strerror
## 			else:
## 				msg = msg[1]
## 			sys.stderr.write('%s: cannot open: %s\n' % (fn, msg))
## 			sys.exit(2)

## 	# patch the module search path
## 	# so we are less dependent on where we are called
## 	sys.path.append(findfile('lib'))
## 	sys.path.append(findfile('video'))

##	import mimetypes, grins_mimetypes
##	mimetypes.types_map.update(grins_mimetypes.mimetypes)

	import Channel
	#
	stats = 0
	#
##	import Help
##	if hasattr(Help, 'sethelpprogram'):
##		import settings
##		if settings.get('lightweight'):
##			Help.sethelpprogram('light')
##		else:
##			Help.sethelpprogram('editor')
	for opt, arg in opts:
		if opt == '-s':
			stats = 1
		if opt == '-n':
			Channel.disable_prearm()
		if opt == '-h':
			import Help
			Help.sethelpdir(arg)
	#

	m = Main(opts, files)

	if splash is not None:
		splash.unsplash()


	try:
		try:
			m.run()
		except kbd_int:
			print 'Interrupt.'
			m.close_callback()
		except SystemExit, sts:
			if type(sts) is type(m):
				if sts.code:
					print 'Exit %d' % sts.code
			elif sts:
				print 'Exit', sts
			sys.last_traceback = None
			sys.exc_traceback = None
			sys.exit(sts)
		except:
			sys.stdout = sys.stderr
			if hasattr(sys, 'exc_info'):
				exc_type, exc_value, exc_traceback = sys.exc_info()
			else:
				exc_type, exc_value, exc_traceback = sys.exc_type, sys.exc_value, sys.exc_traceback
			import traceback, pdb
			print
			print '\t-------------------------------------------------'
			print '\t| Fatal error - Please mail this output to      |'
			print '\t| grins-support@oratrix.com with a description  |'
			print '\t| of the circumstances.                         |'
			print '\t-------------------------------------------------'
			print '\tVersion:', version
			print
			traceback.print_exception(exc_type, exc_value, None)
			traceback.print_tb(exc_traceback)
			print
			pdb.post_mortem(exc_traceback)
	finally:
		import windowinterface
		windowinterface.close()
		if stats:
			import MMNode
			MMNode._prstats()


# A copy of cmif.findfile().  It is copied here rather than imported
# because the result is needed to extend the Python search path to
# find the cmif module!

# WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
# *********  If you change this, also change ../lib/cmif.py   ***********
# WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING

cmifpath = None

def findfile(name):
	global cmifpath
	if os.path.isabs(name):
		return name
	if cmifpath is None:
		if os.environ.has_key('CMIFPATH'):
			import string
			var = os.environ['CMIFPATH']
			cmifpath = string.splitfields(var, ':')
		elif os.environ.has_key('CMIF'):
			cmifpath = [os.environ['CMIF']]
		else:
			import sys
			cmifpath = [os.path.dirname(sys.executable)]
			try:
				link = os.readlink(sys.executable)
			except (os.error, AttributeError):
				pass
			else:
				cmifpath.append(os.path.dirname(os.path.join(os.path.dirname(sys.executable), link)))
	for dir in cmifpath:
		fullname = os.path.join(dir, name)
		if os.path.exists(fullname):
			return fullname
	return name

main()
