# Form definition file generated with fdesign. 

from FL import *
import fl


# Form definition file generated with fdesign. 

def mk_form_help_form (mod):
	help_form = fl.make_form(NO_BOX,550.0,750.0)
	mod.help_form = help_form
	#
	obj = help_form.add_box(UP_BOX,0.0,0.0,550.0,750.0,'')
	#
	topic = help_form.add_browser(HOLD_BROWSER,220.0,660.0,320.0,80.0,'Topic:')
	topic.col1, topic.col2 = 15, 3
	topic.align = ALIGN_LEFT
	topic.set_call_back(mod.cb_topic, 0)
	mod.topic = topic
	#
	help = help_form.add_browser(SELECT_BROWSER,10.0,10.0,530.0,630.0,'')
	help.col1, help.col2 = 15, 3
	help.set_call_back(mod.cb_help, 0)
	mod.help = help
	#
	return help_form


# -------- END of FORM help_form -------------#

