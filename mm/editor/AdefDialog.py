#
# AdefDialog - A more-or-less modal dialog that does keep gl events
# coming in, though, so we can define anchors.

import fl
import FL
import flp

class Struct(): pass
data = Struct()
data.initialized = 0

cancel = 'AdefDialog.cancel'

def run(str):
	if not data.initialized:
		form = flp.parse_form('AdefDialogForm', 'form')
		flp.create_full_form(data, form)
		data.initialized = 1
	data.label.label = str + '\nor click "whole node" button'
	fl.deactivate_all_forms()
	data.form.show_form(FL.PLACE_MOUSE, 1, '')
	obj = fl.do_forms()
	data.form.hide_form()
	fl.activate_all_forms()
	if obj == data.cancel_button:
		raise cancel
	elif obj == data.ok_button:
		return 1
	elif obj == data.whole_button:
		return 0
	else:
		print 'AdefDialog: funny object returned: ', obj
		return 0
