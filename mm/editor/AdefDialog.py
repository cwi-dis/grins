#
# AdefDialog - A more-or-less modal dialog that does keep gl events
# coming in, though, so we can define anchors or other squares

import fl
import FL
import flp

class Struct: pass
adata = Struct()
wdata = Struct()
adata.initialized = 0
wdata.initialized = 0

cancel = 'AdefDialog.cancel'

def anchor(str):
	if not adata.initialized:
		form = flp.parse_form('AdefDialogForm', 'aform')
		flp.create_full_form(adata, form)
		adata.initialized = 1
	adata.label.label = str + '\nor click "whole node" button'
	fl.deactivate_all_forms()
	adata.aform.show_form(FL.PLACE_MOUSE, 1, '')
	obj = fl.do_forms()
	adata.aform.hide_form()
	fl.activate_all_forms()
	if obj == adata.cancel_button:
		raise cancel
	elif obj == adata.ok_button:
		return 1
	elif obj == adata.whole_button:
		return 0
	else:
		print 'AdefDialog: funny object returned: ', obj
		return 0

def window(str):
	if not wdata.initialized:
		form = flp.parse_form('AdefDialogForm', 'wform')
		flp.create_full_form(wdata, form)
		wdata.initialized = 1
	wdata.label.label = 'Select position for channel\n'+str
	fl.deactivate_all_forms()
	wdata.wform.show_form(FL.PLACE_MOUSE, 1, '')
	obj = fl.do_forms()
	wdata.wform.hide_form()
	fl.activate_all_forms()
	if obj <> wdata.ok_button:
		print 'AdefDialog: funny object returned: ', obj
	return

