import fl
import help_form
import posix
from Dialog import BasicDialog
from ViewDialog import ViewDialog

class HelpWindow() = ViewDialog(), BasicDialog():
    def init(self, (dirname, root)):
    	self = ViewDialog.init(self, 'help_')
	self = BasicDialog.init(self, (0, 0, 'Help'))
    	self.root = root
	self.dirname = dirname + '/'
	self.topics = []
	for topic in posix.listdir(dirname):
		if topic[:1] not in ('.', '#') and topic[-1:] <> '~':
			self.topics.append(topic)
	self.topics.sort()
	for line in self.topics:
	    self.topic.add_browser_line(line)
	return self
    def make_form(self):
	# This sets self.topic and self.help:
	self.form = help_form.mk_form_help_form(self)
    def givehelp(self, topic):
	for i in range(0,len(self.topics)):
	    if self.topics[i] = topic:
		self.topic.deselect_browser()
		self.topic.select_browser_line(i+1)
		self.help.load_browser(self.dirname + self.topics[i-1])
		self.show()
		return
	self.help.clear_browser()
	fl.message('No such help topic:', topic, '')
	self.show()
    def cb_topic(self, arg):
	i = arg[0].get_browser()
	if i = 0:
	    self.help.clear_browser()
	else:
	    self.help.load_browser(self.dirname + self.topics[i-1])
    def winshut(self):
	self.hide()
    def cb_exit(self, arg):
	self.hide()
