__version__ = "$Id$"

from Channel import Channel
import MMAttrdefs
import string
import os
import urllib

if os.name == 'posix':
	ProgramAttrname = 'unixprog'
elif os.name == 'mac':
	ProgramAttrname = 'macprog'
elif os.name == 'win':
	ProgramAttrname = 'winprog'
else:
	print 'Warning: unknown OS for ExternalChannel'
	ProgramAttrname = 'unixprog'

class ExternalChannel(Channel):
	
	node_attrs = Channel.node_attrs + ['macprog', 'unixprog', 'winprog',
					   'wanturl']
	
	def __init__(self, name, attrdict, scheduler, ui):
		self.pid = None
		Channel.__init__(self, name, attrdict, scheduler, ui)

	def do_play(self, node):
		self.pid = None
		progname = MMAttrdefs.getattr(node, ProgramAttrname)
		if not progname:
			self.errormsg('No application specified')
			return
		type = node.GetType()
		if type != 'ext':
			self.errormsg(node, 'Node must be external')
			return
		argument = self.getfileurl(node)
		wanturl = MMAttrdefs.getattr(node, 'wanturl')
		if not wanturl:
			argument = urllib.urlretrieve(argument)[0]
		startprog(progname, argument, wanturl)

if os.name == 'posix':
	
	def startprog(prog, arg, argisurl):
		arglist = string.split(prog)
		arglist.append(arg)
		try:
			pid = os.fork()
		except os.error, msg:
			print 'fork:', msg
			return None
		if pid == 0: # Child
			os.execvp(arglist[0], arglist)
			
elif os.name == 'mac':
	
	import MacOS
	import macfs
	import aetools
	import Required_Suite

	class ExtApp(aetools.TalkTo, Required_Suite.Required_Suite):
		pass
		
	def startprog(prog, file, argisurl):
		if argisurl:
			print 'ExternalChannel: URL passing not implemented yet'
		try:
			prog = ExtApp(prog, start=1)
		except (aetools.Error, MacOS.Error), arg:
			print 'ExternalChannel: Cannot start app', prog, arg
		try:
			fss = macfs.FSSpec(file)
		except MacOS.Error, arg:
			print 'ExternalChannel: Cannot obtain fsspec', file, arg
		try:
			prog.open(fss)
		except (aetools.Error, MacOS.Error), arg:
			print 'ExternalChannel: Cannot open file', file, arg
			
elif os.name == 'win':
	
	def startprog(prog, file, argisurl):
		print 'Not yet implemented'
