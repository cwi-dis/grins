import dialogs, windowinterface, EVENTS

message = 'Use left mouse button to draw a box.\n' + \
	  'Click `Done\' when ready or `Cancel\' to cancel.'

def create_box(window, msg, *box):
	if len(box) == 1 and type(box) == type(()):
		box = box[0]
	if len(box) not in (0, 4):
		raise TypeError, 'bad arguments'
	if len(box) == 0:
		box = None
	windowinterface.startmonitormode()
	display = window._active_display_list
	window.pop()
	if msg:
		msg = msg + '\n\n' + message
	else:
		msg = message
	dialog = dialogs.Dialog().init((msg, '!Done', 'Cancel'))
	while not box:
		win, ev, val = windowinterface.readevent()
		if win == window and ev == EVENTS.Mouse0Press:
			box = window.sizebox((val[0], val[1], 0, 0), 0, 0)
			break
		else:
			r = dialog.checkevent(win, ev, val)
			if r:
				dialog.close()
				windowinterface.endmonitormode()
				return None
	if display and not display.is_closed():
		d = display.clone()
	else:
		d = window.newdisplaylist()
	d.fgcolor(255, 0, 0)
	d.drawbox(box)
	d.render()
	while 1:
		win, ev, val = windowinterface.readevent()
		if win == window and ev == EVENTS.Mouse0Press:
			x, y = val[0:2]
			if box[0] + box[2]/4 < x < box[0] + box[2]*3/4:
				constrainx = 1
			else:
				constrainx = 0
			if box[1] + box[3]/4 < y < box[1] + box[3]*3/4:
				constrainy = 1
			else:
				constrainy = 0
			if display and not display.is_closed():
				display.render()
			d.close()
			if constrainx and constrainy:
				box = window.movebox(box, 0, 0)
			else:
				if x < box[0] + box[2] / 2:
					x0 = box[0] + box[2]
					w = - box[2]
				else:
					x0 = box[0]
					w = box[2]
				if y < box[1] + box[3] / 2:
					y0 = box[1] + box[3]
					h = -box[3]
				else:
					y0 = box[1]
					h = box[3]
				box = window.sizebox((x0, y0, w, h), \
					  constrainx, constrainy)
			if display and not display.is_closed():
				d = display.clone()
			else:
				d = window.newdisplaylist()
			d.fgcolor(255, 0, 0)
			d.drawbox(box)
			d.render()
		else:
			r = dialog.checkevent(win, ev, val)
			if r:
				dialog.close()
				if display and not display.is_closed():
					display.render()
				d.close()
				windowinterface.endmonitormode()
				if r == '!Done':
					return box
				return None
