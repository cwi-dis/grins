#
# Test the PICT button control.
#

import Dlg
import Res
import sys
import MacOS

DIALOG_ID=512

I_DISABLE=1
I_ENABLE=2
I_RESET=3
I_OK=4
I_VALUE=5
I_CNTL=6

def run():
	d = Dlg.GetNewDialog(DIALOG_ID, -1)
	if not d:
		print "Cannot find dialog"
		sys.exit(1)
	tp, value_handle, rect = d.GetDialogItem(I_VALUE)
	tp, h, rect = d.GetDialogItem(I_CNTL)
	button_cntl = h.as_Control()
	while 1:
		value = button_cntl.GetControlValue()
		Dlg.SetDialogItemText(value_handle, 'Value: %s'%value)
		
		n = Dlg.ModalDialog(None)
		
		if n == I_DISABLE:
			button_cntl.HiliteControl(255)
		if n == I_ENABLE:
			button_cntl.HiliteControl(0)
		if n == I_RESET:
			value = button_cntl.GetControlMinimum()
			button_cntl.SetControlValue(value)
		if n == I_OK:
			return
		if n == I_CNTL:
			MacOS.SysBeep()
			
def main():
	Res.OpenResFile("testpictbutton.rsrc")
	run()
	
if __name__ == '__main__':
	main()
