import fl
import help_form
import posix
import string
import sys
from Dialog import BasicDialog
from ViewDialog import ViewDialog

class HelpWindow() = ViewDialog(), BasicDialog():
    def init(self, (dirname, toplevel)):
    	self = ViewDialog.init(self, 'help_')
	self = BasicDialog.init(self, (0, 0, 'Help'))
    	self.toplevel = toplevel
    	self.root = toplevel.root # For ViewDialog
	self.dirname = dirname + '/'
	self.topics = None
	return self
    def inittopics(self):
	if self.topics <> None: return
	self.topics = []
	for topic in posix.listdir(self.dirname):
		if topic[:1] not in ('.', '#') and topic[-1:] <> '~':
			self.topics.append(topic)
	self.topics.sort()
	for line in self.topics:
	    self.topic.add_browser_line(line)
	self.curtopic = ''
    def show(self):
	self.inittopics()
    	BasicDialog.show(self)
    	self.toplevel.checkviews()
    def hide(self):
    	BasicDialog.hide(self)
    	self.toplevel.checkviews()
    def make_form(self):
	# This sets self.topic and self.help:
	self.form = help_form.mk_form_help_form(self)
    def givehelp(self, topic):
	self.inittopics()
	if type(topic) = type(()):
	    topic, subtopic = topic
	else:
	    subtopic = ''
	for i in range(0,len(self.topics)):
	    if self.topics[i] = topic:
		self.topic.deselect_browser()
		self.topic.select_browser_line(i+1)
		self.topic.set_browser_topline(i+1)
		self.help.load_browser(self.dirname + topic)
		self.curtopic = topic
		if subtopic:
                    j = findtopicline(self.dirname + topic, subtopic)
                    if j:
                        self.help.set_browser_topline(j)
                        self.help.select_browser_line(j)
		self.show()
		return
	fl.show_message('No such help topic:', topic, '')
	if self.curtopic:
	    topic, self.curtopic = self.curtopic, ''
	    self.givehelp(topic)
	else:
	    self.help.clear_browser()
	    self.show()
    def cb_topic(self, arg):
	i = arg[0].get_browser()
	if i = 0:
	    self.help.clear_browser()
	else:
	    self.givehelp(self.topics[i-1])
    def cb_help(self, arg):
        i = arg[0].get_browser()
        if i:
            i = arg[0].get_browser_line(i)
            topic, subtopic = parsetopic(i)
            if topic:
                self.givehelp((topic, subtopic))

    def winshut(self):
	self.hide()
    def cb_exit(self, arg):
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
	if s[:sl] = str:
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

def main():
    Help = HelpWindow().init('.', None)
    if len(sys.argv) > 1:
	Help.givehelp(sys.argv[1])
    else:
	Help.show()
    try:
	while 1:
	    Help.run()
    except Exit:
	    pass

