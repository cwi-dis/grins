# Help window

# Interface:
# (1) optionally call sethelpdir(dirname) with a directory name argument;
# (2) If the user presses a Help button, call showhelpwindow().
# When the help window is already open, it is popped up.


import fl
import os
import string
import flp
from Dialog import BasicDialog


helpdir = None # Directory where the help files live

def sethelpdir(dirname):
    global helpdir
    helpdir = dirname


helpwindow = None # Help window instance, once opened

def showhelpwindow():
    global helpwindow, helpdir
    if helpwindow == None:
	if helpdir == None:
	    import cmif
	    helpdir = cmif.findfile('help')
	helpwindow = HelpWindow().init(helpdir)
    helpwindow.show()


class HelpWindow(BasicDialog):
    
    def init(self, dirname):
	self = BasicDialog.init(self, 0, 0, 'Help')
	self.dirname = dirname + '/'
	self.topics = None
	self.return_stack = []
	return self
    
    def __repr__(self):
	return '<HelpWindow instance, dirname=' + `self.dirname` + '>'
    
    def inittopics(self):
	if self.topics <> None: return
	self.topics = []
	try:
	    files = os.listdir(self.dirname)
	except os.error:
	    files = []
	for topic in files:
	    if topic[:1] not in '.,#@' and topic[-1:] <> '~' and \
			os.path.isfile(self.dirname + topic):
		self.topics.append(topic)
	self.topics.sort()
	for line in self.topics:
	    self.topic.add_browser_line(line)
	self.curtopic = ''
	if not self.topics:
	    print 'Sorry, no help topics found'
    
    def show(self):
	self.inittopics()
    	BasicDialog.show(self)
    
    ##def hide(self):
    ##    BasicDialog.hide(self)
    
    def make_form(self):
	# This sets self.topic and self.help:
	ftemplate = flp.parse_form('HelpForm', 'form')
	flp.create_full_form(self, ftemplate)
	self.button_return.hide_object()
    
    def givehelp(self, topic, totop):
	self.inittopics()
	if type(topic) == type(()):
	    topic, subtopic = topic
	else:
	    subtopic = ''
	#
	# Yucky: if the subtopic is numeric we assume that this
	# is a return, and we don't stack the current help page.
	if self.curtopic <> '' and type(subtopic) <> type(1):
	    num = self.help.get_browser()
	    self.return_stack.insert(0,(self.curtopic,num))
	    self.button_return.show_object()
	for i in range(0,len(self.topics)):
	    if self.topics[i] == topic:
		self.topic.deselect_browser()
		self.topic.select_browser_line(i+1)
		if totop: self.topic.set_browser_topline(i+1)
		self.help.load_browser(self.dirname + topic)
		self.curtopic = topic
		if subtopic:
		    if type(subtopic) == type(1):
			j = subtopic
		    else:
			j = findtopicline(self.dirname + topic, subtopic)
                    if j:
			if totop: self.help.set_browser_topline(j)
			self.help.select_browser_line(j)
		self.show()
		return
	fl.show_message('No such help topic:', topic, '')
	if self.curtopic:
	    topic, self.curtopic = self.curtopic, ''
	    self.givehelp(topic, 0)
	else:
	    self.help.clear_browser()
	    self.show()
    
    def cb_return(self, (obj, arg)):
	if self.return_stack:
	    topic = self.return_stack[0]
	    del self.return_stack[0]
	    if not self.return_stack:
		self.button_return.hide_object()
	    self.givehelp(topic, 1)
    
    def cb_topic(self, (obj, arg)):
	i = obj.get_browser()
	if i == 0:
	    self.help.clear_browser()
	else:
	    self.givehelp(self.topics[i-1], 0)
    
    def cb_help(self, (obj, arg)):
        i = obj.get_browser()
        if i:
            i = obj.get_browser_line(i)
            topic, subtopic = parsetopic(i)
            if topic:
                self.givehelp((topic, subtopic), 1)
    
    def winshut(self):
	self.hide()
    
    def cb_exit(self, (obj, arg)):
	self.hide()


def findtopicline(file, str):
    str = str + ':'
    sl = len(str)
    f = open(file, 'r')
    i = 0
    s = 'x'
    while s <> '':
	i = i + 1
	s = f.readline()
	if s[:sl] == str:
	    return i
    return 0


def parsetopic(s):
    try:
	f = string.index(s,'[')
	t = string.index(s,']')
	topic = s[f+1:t]
	subtopic = ''
	if ',' in topic:
	    f = string.index(topic, ',')
	    subtopic = topic[f+1:]
	    topic = topic[:f]
	return string.strip(topic), string.strip(subtopic)
    except string.index_error:
	return '',''


# This is mostly Jack's code, so...
# Local variables:
# py-indent-offset: 4
# end:
