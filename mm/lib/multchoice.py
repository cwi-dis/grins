__version__ = "$Id$"

# Multiple choice modal dialog using FORMS.

import fl, FL
import string

Tuple = type(())

# Parametrizations -- change these to make it look right
# (Ideally we should use the font manager to make these calculations...)

BUTHEIGHT = 30				# Height of a button
HMARGIN = 5				# Left and right margin around buttons
VMARGIN = 5				# Top and bottom " " "
CHARWIDTH = 10				# Average character width
TEXTHEIGHT = 20				# Height of a text line
EXTRASPACE = 20				# Extra space aroud text in buttons


# Arguments:
# prompt    - a prompt string displayed above the menu; may contain newlines
# list      - a list of (string, colorindex) pairs and just strings;
#             no colorindex or None means use the default color
# defindex  - the index of the default item in the list, -1 for no default;
#
# Return value: the index of the selected item (there is no escape unless
# the caller provides a 'Cancel' item).

def multchoice(prompt, list, defindex):

	nchars = 10
	
	if prompt:
		promptlines = string.splitfields(prompt, '\n')
		promptheight = TEXTHEIGHT * len(promptlines) + 2*VMARGIN
		for line in promptlines:
			nchars = max(nchars, len(line))
	else:
		promptheight = 0
	
	for item in list:
		if type(item) is Tuple:
			name, colorindex = item
		else:
			name = item
		nchars = max(nchars, len(name))
	
	butwidth = CHARWIDTH*nchars + EXTRASPACE
	width = butwidth + 2*HMARGIN
	height = len(list)*BUTHEIGHT + 2*VMARGIN + promptheight
	
	form = fl.make_form(FL.UP_BOX, width, height)
	
	pos = height - VMARGIN - promptheight

	if prompt:
		obj = form.add_text(FL.NO_BOX, \
			HMARGIN, pos, butwidth, promptheight, prompt)
	
	buttons = []
	for i in range(len(list)):
		pos = pos - BUTHEIGHT
		item = list[i]
		if type(item) is Tuple:
			name, colorindex = item
		else:
			name, colorindex = item, None
		if i == defindex:
			but = FL.RETURN_BUTTON
		else:
			but = FL.NORMAL_BUTTON
		obj = form.add_button(but, \
			HMARGIN, pos, butwidth, BUTHEIGHT, name)
		obj.boxtype = FL.FRAME_BOX
		if colorindex is not None:
			obj.col1 = colorindex
		buttons.append(obj)
	
	fl.deactivate_all_forms()
	while fl.check_forms():
		pass # Empty the queue!
	form.show_form(FL.PLACE_MOUSE, FL.FALSE, 'multchoice')
	choice = fl.do_forms() # Must be one of our buttons
	form.hide_form()
	fl.activate_all_forms()

	for b in buttons:
		b.delete_object()
	
	return buttons.index(choice)
