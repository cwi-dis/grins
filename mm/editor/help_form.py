# Form definition file generated with fdesign. 

from FL import *
import fl


# Form definition file generated with fdesign. 

def mk_form_help_form (mod) : 
	help_form = fl.make_form(NO_BOX,547.0,800.0)
	mod.help_form = help_form
	#
	obj = help_form.add_box(UP_BOX,0.0,0.0,547.0,800.0,'')
	#
	topic = help_form.add_browser(HOLD_BROWSER,220.0,660.0,320.0,80.0,'Topic:')
	topic.col1, topic.col2 = 10, 3
	topic.align = ALIGN_LEFT
	topic.set_call_back(mod.cb_topic, 0)
	mod.topic = topic
	#
	help = help_form.add_browser(NORMAL_BROWSER,10.0,10.0,530.0,630.0,'')
	help.col1, help.col2 = 10, 3
	mod.help = help
	#
	obj = help_form.add_text(NORMAL_TEXT,110.0,760.0,320.0,30.0,'HELP')
	obj.boxtype = BORDER_BOX
	obj.align = ALIGN_CENTER
	obj.lstyle = BOLD_STYLE
	#
	exit = help_form.add_button(NORMAL_BUTTON,20.0,660.0,140.0,80.0,'Exit help')
	exit.lstyle = BOLD_STYLE
	exit.set_call_back(mod.cb_exit, 0)
	mod.exit = exit
	#
	return help_form


# -------- END of FORM help_form -------------#

