"""Test windowinterface fixed dialogs, editor specifics"""

__version__ = "$Id$"

import sys
import os

if os.name == 'posix':
	sys.path.append("../lib")
	import X_window
	window = X_window
elif os.name == 'mac':
	sys.path.append("::lib")
	sys.path.append("::mac")
	import mac_window
	window = mac_window
# etc...

done="done"
cb_called=0
def cb_ok(filename):
	global cb_called
	cb_called = 1
	print "Your answer:",filename
	raise done

def cb_cancel():
	global cb_called
	cb_called = 1
	print "You selected cancel"
	raise done
	
print "First we will ask you to select a Python source in the current dir"
cb_called = 0
fd = window.FileDialog("Select Python source", ".", "*.py", "",
		cb_ok, cb_cancel, existing=1)
try:
	if not cb_called:
		window.mainloop()
except done:
	fd.close()
	del fd

print "Next we will ask you to give a name for a new .py file"
cb_called = 0
fd = window.FileDialog("Select Python output file", ".", "*.py", "",
		cb_ok, cb_cancel, existing=0)
try:
	if not cb_called:
		window.mainloop()
except done:
	fd.close()
	del fd

print "Now we will ask you to select a beer"
sd = window.SelectionDialog("List of beers", "Favourite",
			    ["Heineken", "Amstel", "Brand", "Alfa", "Leeuw",
			     "Henninger", "Bavaria", "Bass", "Miller",
			     "Budwiser", "Budvar"], "none, really")
sd.OkCallback = cb_ok
sd.CancelCallback = cb_cancel
try:
	window.mainloop()
except done:
	sd.close()
	del sd

print 'Modal and modeless messages and questions'
def answer(arg):
	print 'You answered', arg
	
window.showmessage('A modeless message. Stop mainloop with cmd.', grab=0)
window.showmessage('A modeless question', mtype='question', grab=0,
	callback=(answer, ('ok',)), cancelCallback=(answer, ('cancel',)))
	
	
try:
	window.mainloop()
except KeyboardInterrupt:
	pass
window.showmessage('A modal message', grab=1)
window.showmessage('A modal question', mtype='question', grab=1,
	callback=(answer, ('ok',)), cancelCallback=(answer, ('cancel',)))
	

print "Now you should say something to me"
id = window.InputDialog("Say something", "I have nothing to say", cb_ok)
try:
	window.mainloop()
except done:
	id.close()
	del id
	
