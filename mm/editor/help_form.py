# Form definition file generated with fdesign. 

from FL import *
import fl


# Form definition file generated with fdesign. 

def mk_form_help_form (mod):
	help_form = fl.make_form(NO_BOX,530.0,750.0)
	mod.help_form = help_form
	#
	obj = help_form.add_box(UP_BOX,0.0,0.0,530.0,750.0,'')
	#
	topic = help_form.add_browser(HOLD_BROWSER,200.0,650.0,320.0,90.0,'')
	topic.col1, topic.col2 = 15, 3
	topic.align = ALIGN_LEFT
	topic.set_call_back(mod.cb_topic, 0)
	mod.topic = topic
	#
	help = help_form.add_browser(SELECT_BROWSER,10.0,10.0,510.0,630.0,'')
	help.col1, help.col2 = 15, 3
	help.set_call_back(mod.cb_help, 0)
	mod.help = help
	#
	obj = help_form.add_text(NORMAL_TEXT,10.0,700.0,180.0,40.0,'Click on a topic\nto get help')
	obj.align = ALIGN_CENTER
	#
	button_return = help_form.add_button(NORMAL_BUTTON,10.0,650.0,180.0,40.0,'Return to previous')
	button_return.set_call_back(mod.cb_return, 0)
	mod.button_return = button_return
	#
	return help_form


# -------- END of FORM help_form -------------#

