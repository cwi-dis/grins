__version__ = "$Id$"

# Main program for the CMIF player.

import sys
import os

NUM_RECENT_FILES = 10

def usage(msg):
	sys.stdout = sys.stderr
	print msg
	print 'usage: grins file ...'
	print 'file ...   : one or more SMIL or CMIF files or URLs'
	sys.exit(2)

from MainDialog import MainDialog
from usercmd import *

from version import version

# empty document, used to get a working skin
EMPTYDOC = 'data:application/smil,<smil/>'

class Main(MainDialog):
	def __init__(self):
		import windowinterface, features
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

		self.do_init()
##		self.recent_file_list = []
				
	def do_init(self, license=None):
		# We ignore the license, not needed in the player
		import MMurl, windowinterface
		self._tracing = 0
		self.nocontrol = 0	# For player compatability
		self._closing = 0
		self.tops = []
		self.last_location = ''
		self.commandlist = [
			OPEN(callback = (self.open_callback, ())),
			OPENFILE(callback = (self.openfile_callback, ())),
##			OPEN_RECENT(callback = self.open_recent_callback),	# Dynamic cascade
##			RELOAD(callback = (self.reload_callback, ())), 
##			PREFERENCES(callback = (self.preferences_callback, ())),
##			CHECKVERSION(callback=(self.checkversion_callback, ())),
			CHOOSESKIN(callback = (self.skin_callback, ())),
			CHOOSECOMPONENTS(callback = (self.components_callback, ())),
			EXIT(callback = (self.close_callback, ())),
			]
		import settings
##		if hasattr(windowinterface, 'is_embedded') and windowinterface.is_embedded():
##			settings.factory_defaults()
		MainDialog.__init__(self, 'GRiNS')
		if settings.get('skin'):
			self.openURL_callback(EMPTYDOC)
##		self._update_recent(None)

	def skin_callback(self):
		import settings
		oldskin = settings.get('skin')
		MainDialog.skin_callback(self)
		newskin = settings.get('skin')
		if newskin and oldskin != newskin:
			if self.tops:
				url = self.tops[0].url
			else:
				url = EMPTYDOC
			self.openURL_callback(url)

	def openURL_callback(self, url):
		import windowinterface
		windowinterface.setwaiting()
		from MMExc import MSyntaxError
		import TopLevel
		self.last_location = url
		try:
			top = TopLevel.TopLevel(self, url)
		except IOError:
			import windowinterface
			windowinterface.showmessage('Cannot open: %s' % url)
		except MSyntaxError:
			import windowinterface
			windowinterface.showmessage('Parse error in document: %s' % url)
		else:
			while self.tops:
				self.tops[0].close_callback()
			self.tops.append(top)
			top.show()
			top.player.show()
##			self._update_recent(url)
			top.player.play_callback()

##	def open_recent_callback(self, url):
##		self.openURL_callback(url)
		
	def _update_recent(self, url):
		pass
##		if url:
##			self.add_recent_file(url)
##		doclist = self.get_recent_files()
##		self.set_recent_list(doclist)

##	def get_recent_files(self):
##		if not hasattr(self, 'set_recent_list'):
##			return
##		import settings
##		import posixpath
##		recent = settings.get('recent_documents')
##		doclist = []
##		for url in recent:
##			base = posixpath.basename(url)
##			doclist.append( (base, (url,)))
##		return doclist

##	def add_recent_file(self, url):
##		# Add url to the top of the recent file list.
##		import windowinterface
##		assert url
##		import settings
##		recent = settings.get('recent_documents')
##		if url in recent:
##			recent.remove(url)
##		recent.insert(0, url)
##		if len(recent) > NUM_RECENT_FILES:
##			recent = recent[:NUM_RECENT_FILES]
##		settings.set('recent_documents', recent)
##		settings.save()

	def close_callback(self, exitcallback=None):
		for top in self.tops[:]:
			top.destroy()
		import windowinterface
		windowinterface.getmainwnd().destroy()

##	def preferences_callback(self):
##		import Preferences
##		Preferences.showpreferences(1, self.prefschanged)

##	def prefschanged(self):
##		for top in self.tops:
##			top.prefschanged()

##	def checkversion_callback(self):
##		import MMurl
##		import version
##		import windowinterface
##		import settings
##		url = 'http://www.oratrix.com/indir/%s/updatecheck.txt'%version.shortversion
##		try:
##			fp = MMurl.urlopen(url)
##			data = fp.read()
##			fp.close()
##		except:
##			windowinterface.showmessage('Unable to check for upgrade. You can try again later, or visit www.oratrix.com with your webbrowser.')
##			print "Could not load URL", url
##			return
##		data = data.strip()
##		if not data:
##			windowinterface.showmessage('You are running the latest version of the software')
##			return
##		cancel = windowinterface.GetOKCancel('There appears to be a newer version!\nDo you want to know more?')
##		if cancel:
##			return
##		# Pass the version and the second item of the license along.
##		id = settings.get('license').split('-')[1]
##		url = '%s?version=%s&id=%s'%(data, version.shortversion, id)
##		windowinterface.htmlwindow(url)

	def closetop(self, top):
		if self._closing:
			return
		self._closing = 1
		self.tops.remove(top)
		top.hide()
		if len(self.tops) == 0:
			# no TopLevels left: exit
			sys.exit(0)
		self._closing = 0

	def run(self):
		import windowinterface
		windowinterface.mainloop()

def main():
	m = Main()
	m.run()
# Call the main program

main()
