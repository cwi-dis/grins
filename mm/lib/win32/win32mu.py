__version__ = "$Id$"


# Objects
# <draw functions>
# def _win_setcursor(form, cursor):
# def _create_menu(menu, list, menuid, cbdict, acc = None):

from types import *
import win32ui, win32con, win32api
from win32modules import cmifex, cmifex2, win32sdk

####################################################
# Utilities that replace part of cmifex functionality
# and correct some of its drawbacks
# They radically correct the flashing problem (repeated paintings)
# by using the correct device context
# and clipping region returned by windows
# throu BeginPaint. 

# We have indroduced Sdk Gdi objects because
# CPen,CBrush,... are not destroyed properly
# by win32ui

def RGB(l):
	return win32api.RGB(l[0],l[1],l[2])
	
def DrawLine(dc,l,rgb=(0,0,0),width=1,style=win32con.PS_SOLID):
	pen=win32sdk.CreatePen(style,width,RGB(rgb))
	oldpen=dc.SelectObjectFromHandle(pen)
	dc.MoveTo(l[:2])
	dc.LineTo(l[2:])
	dc.SelectObjectFromHandle(oldpen)
	win32sdk.DeleteObject(pen)

def FillPolygon(dc,pts,rgb):
	br=win32sdk.CreateBrush(win32con.BS_SOLID,RGB(rgb),0)
	pen=win32sdk.CreatePen(win32con.PS_SOLID,0,RGB(rgb))
	oldpen=dc.SelectObjectFromHandle(pen)
	oldbr=dc.SelectObjectFromHandle(br)
	pm = dc.SetPolyFillMode(win32con.WINDING);
	dc.Polygon(pts);
	dc.SetPolyFillMode(pm);
	dc.SelectObjectFromHandle(oldpen)
	dc.SelectObjectFromHandle(oldbr)
	win32sdk.DeleteObject(pen)
	win32sdk.DeleteObject(br)


def DrawRectanglePath(dc,rc):
	dc.MoveTo((rc[0],rc[1]))
	dc.LineTo((rc[2],rc[1]))
	dc.LineTo((rc[2],rc[3]))
	dc.LineTo((rc[0],rc[3]))
	dc.LineTo((rc[0],rc[1]))

def DrawRectangle(dc,rc,rgb,st):
	if st == "d":
		pen=win32sdk.CreatePen(win32con.PS_SOLID,0,win32api.RGB(0,0,0))
		oldpen=dc.SelectObjectFromHandle(pen)
		DrawRectanglePath(dc,rc)
		dc.SelectObjectFromHandle(oldpen)
		win32sdk.DeleteObject(pen)
	else:
		pass	
		br=win32sdk.CreateBrush(win32con.BS_SOLID,RGB(rgb),0)	
		dc.FrameRectFromHandle(rc,br)
		win32sdk.DeleteObject(br)
		

# replaces: cmifex.SetSiblings
def SetWndStyle(wnd,flag):
	style = wnd.GetWindowLong(win32con.GWL_EXSTYLE)
	if flag==1:
		style = style | win32con.WS_EX_TRANSPARENT;
	elif flag==0:
		style = style & ~win32con.WS_EX_TRANSPARENT;
	wnd.SetWindowLong(win32con.GWL_EXSTYLE,style)

# replaces: cmifex.DrawLines			
def DrawLines(dc,ll,rgb):
	pen=win32sdk.CreatePen(win32con.PS_SOLID,0,RGB(rgb))
	oldpen=dc.SelectObjectFromHandle(pen)
	dc.Polyline(ll)
	dc.SelectObjectFromHandle(oldpen)
	win32sdk.DeleteObject(pen)

####################################################

[ARROW, WAIT, HAND, START, G_HAND, U_STRECH,
D_STRECH, L_STRECH, R_STRECH, UL_STRECH, 
UR_STRECH, DR_STRECH, DL_STRECH, PUT] = range(14)

win32Cursors = { 'hand':HAND, 'watch':WAIT, '':ARROW, 'start':START,
				'g_hand':G_HAND, 'ustrech':U_STRECH, 'dstrech':D_STRECH,
				'lstrech':L_STRECH, 'rstrech':R_STRECH, 'ulstrech':UL_STRECH,
				'urstrech':UR_STRECH, 'drstrech':DR_STRECH,
				'dlstrech':DL_STRECH, 'channel':PUT }

def _win_setcursor(form, cursor):
	keys = win32Cursors.keys()
	if not cursor in keys:
		cursor = ''
	cmifex.SetCursor(win32Cursors[cursor])
	return
	if cursor == 'watch':
		form.DefineCursor(toplevel._watchcursor)
	elif cursor == 'channel':
		form.DefineCursor(toplevel._channelcursor)
	elif cursor == 'link':
		form.DefineCursor(toplevel._linkcursor)
	elif cursor == 'stop':
		form.DefineCursor(toplevel._stopcursor)
	elif cursor == '':
		form.UndefineCursor()
	else:
		raise error, 'unknown cursor glyph'


####################################################
def _create_menu(menu, list, menuid, cbdict, acc = None):
	accelerator = None
	length = 0
	i = 0
	id = menuid
	dict  = cbdict
	buts = []
	while i < len(list):
		entry = list[i]
		i = i + 1
		if entry is None:
#			dummy = menu.CreateManagedWidget('separator',
#							 Xm.SeparatorGadget,
#							 {})
			cmifex2.AppendMenu(menu, '', 0)
			continue
#		if length == 20 and i < len(list) - 3:
#			entry = ('More', list[i-1:])
#			i = len(list)
#			if acc is not None:
#				entry = ('',) + entry
		length = length + 1
		if type(entry) is StringType:
#			dummy = menu.CreateManagedWidget(
#				'menuLabel', Xm.LabelGadget,
#				{'labelString': entry})
			cmifex2.AppendMenu(menu, entry, id)
			id = id + 1
			buts.append((entry,None))
			continue
		btype = 'p'		# default is pushbutton
		initial = 0
		if acc is None:
			labelString, callback = entry[:2]
			if len(entry) > 2:
				btype = entry[2]
				if len(entry) > 3:
					initial = entry[3]
		else:
			if len(entry)==2:
				accelerator = None
				labelString, callback = entry
			else:
				accelerator, labelString, callback = entry[:3]
			if len(entry) > 3:
				btype = entry[3]
				if len(entry) > 4:
					initial = entry[4]

		if type(callback) is ListType:
#			submenu = menu.CreatePulldownMenu('submenu',
#				{'colormap': colormap,
#				 'visual': visual,
#				 'depth': visual.depth})
#			button = menu.CreateManagedWidget(
#				'submenuLabel', Xm.CascadeButtonGadget,
#				{'labelString': label, 'subMenuId': submenu})
			submenu = cmifex2.CreateMenu()
			temp = _create_menu(submenu, callback, id, dict, acc)
			
			if temp:
				id = temp[0]
				dict2 = temp[1]
				dkeys = dict2.keys()
				for k in dkeys:
					if not dict.has_key(k):
						dict[k] = dict2[k]
			buts.append((labelString, temp[2]))
			cmifex2.PopupAppendMenu(menu, submenu, labelString)
		else:
			buts.append((labelString, None))
			if type(callback) is not TupleType:
				callback = (callback, (labelString,))
			attrs = {'labelString': labelString}
			if accelerator:
				if type(accelerator) is not StringType or \
				   len(accelerator) != 1:
					raise error, 'menu accelerator must be single character'
				acc[accelerator] = callback
				attrs['acceleratorText'] = accelerator
				labelString = labelString + '\t' + accelerator
			#button = menu.CreateManagedWidget('menuLabel',
			#			Xm.PushButtonGadget, attrs)
			#button.AddCallback('activateCallback',
			#		   _generic_callback, callback)
			cmifex2.AppendMenu(menu, labelString, id)
			dict[id] = callback
			if btype == 't':
				cmifex2.CheckMenuItem(menu,id,initial)
			#print "dict-->", dict
			id = id + 1
		
	t = (id, dict, buts)
	return t
##################################