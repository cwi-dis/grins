import sys
import fl
import FL
import help_form
import glwindow
import DEVICE
import gl
import posix

class Struct(): pass

obj = Struct()

Exit = 'Exit'

class HelpWindow() = (glwindow.glwindow)():
    def init(self, dirname):
	self.dirname = dirname + '/'
	self.topics = []
	for topic in posix.listdir(dirname):
		if topic[:1] not in ('.', '#') and topic[-1:] <> '~':
			self.topics.append(topic)
	self.topics.sort()
	self.form = help_form.mk_form_help_form(self)
	for i in self.topics:
	    self.topic.add_browser_line(i)
	self.shown = 0
	return self
    def show(self):
	if self.shown: return
	self.form.show_form(FL.PLACE_SIZE, 1, 'HELP')
	gl.winset(self.form.window)
	gl.winconstraints()
	fl.qdevice(DEVICE.WINSHUT)
	fl.qdevice(DEVICE.WINQUIT)
	glwindow.register(self, self.form.window)
	self.shown = 1
    def hide(self):
	if not self.shown: return
	self.form.hide_form()
	self.shown = 0
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
    def run(self):
	return fl.do_forms()
    def cb_topic(self, arg):
	i = arg[0].get_browser()
	if i = 0:
	    self.help.clear_browser()
	else:
	    self.help.load_browser(self.dirname + self.topics[i-1])
    def winshut(self):
	self.hide()
###	raise Exit
    def cb_exit(self, arg):
	self.hide()
###	raise Exit


def main():
    Help = HelpWindow().init('.')
    if len(sys.argv) > 1:
	Help.givehelp(sys.argv[1])
    else:
	Help.show()
    try:
	while 1:
	    Help.run()
    except Exit:
	    pass

###main()
