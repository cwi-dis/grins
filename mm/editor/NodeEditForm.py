# Form definition file generated with fdesign. 

from FL import *
import fl


# Form definition file generated with fdesign. 

def mk_form_convertform (mod):
	convertform = fl.make_form(NO_BOX,460.0,120.0)
	mod.convertform = convertform
	#
	obj = convertform.add_box(UP_BOX,0.0,0.0,460.0,120.0,'')
	#
	button_cancel = convertform.add_button(RETURN_BUTTON,10.0,10.0,90.0,30.0,'Cancel')
	button_cancel.set_call_back(mod.callback_cancel, 0)
	mod.button_cancel = button_cancel
	#
	button_convert = convertform.add_button(NORMAL_BUTTON,10.0,50.0,90.0,30.0,'Convert')
	button_convert.set_call_back(mod.callback_convert, 0)
	mod.button_convert = button_convert
	#
	input_filename = convertform.add_input(NORMAL_INPUT,180.0,50.0,270.0,30.0,'Filename:')
	input_filename.set_call_back(mod.callback_dummy, 0)
	mod.input_filename = input_filename
	#
	obj = convertform.add_text(NORMAL_TEXT,10.0,90.0,440.0,30.0,'This is an internal node. Convert to external?')
	obj.align = ALIGN_CENTER
	#
	return convertform


# -------- END of FORM convertform -------------#

def mk_form_err (mod,err):
	#
	obj = err.add_box(NO_BOX,0.0,0.0,460.0,40.0,'')
	#
	obj = err.add_text(NORMAL_TEXT,120.0,10.0,220.0,30.0,'File already exists!')
	#
	button_overwrite = err.add_button(NORMAL_BUTTON,330.0,10.0,120.0,30.0,'Overwrite')
	button_overwrite.set_call_back(mod.callback_overwrite, 0)
	mod.button_overwrite = button_overwrite
	#
	return err


# -------- END of FORM err -------------#

