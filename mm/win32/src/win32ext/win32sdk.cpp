// CMIF_ADD
//
// kk@oratrix.com
//
//
// Note that this source file contains embedded documentation.
// This documentation consists of marked up text inside the
// C comments, and is prefixed with an '@' symbol.  The source
// files are processed by a tool called "autoduck" which
// generates Windows .hlp files.
// @doc




#include "stdafx.h"
#include "win32win.h"

#include "moddef.h"
DECLARE_PYMODULECLASS(Win32Sdk);
IMPLEMENT_PYMODULECLASS(Win32Sdk,GetWin32Sdk,"Win32 Sdk Module Wrapper Object");


// @pymethod |PyWin32Sdk|CreateBrush|Creates a brush and returns its handle
// Return Values: A handle to the created brush 
PyObject *
sdk_create_brush(PyObject *self, PyObject *args)
	{
	int n_brush_style;
	int n_hatch;
	long cr_color;
	LOGBRUSH lp;
  
	if (!PyArg_ParseTuple (args, "iil",
						 &n_brush_style,// @pyparm int|style||The brush style.
						 &cr_color,		// @pyparm int|color||The brush color.
						 &n_hatch))		// @pyparm long|hatch||The brush hatching.
		{
		return NULL;
		}

	lp.lbStyle = n_brush_style;
	lp.lbColor = cr_color;
	lp.lbHatch = n_hatch;

	HBRUSH hbr;
	GUI_BGN_SAVE;
	hbr=CreateBrushIndirect (&lp);
	GUI_END_SAVE;
	if(!hbr)RETURN_ERR("CreateBrushIndirect call failed");
	return Py_BuildValue("i",hbr);
	}

// @pymethod |PyWin32Sdk|CreatePen|Creates a pen and returns its handle
// Return Values: A handle to the created pen 
static PyObject *
sdk_create_pen(PyObject *self, PyObject *args)
	{
	int n_pen_style;
	int n_width;
	long cr_color;
	LOGPEN lp;
  
	if (!PyArg_ParseTuple (args, "iil",
						 &n_pen_style, // @pyparm int|style||The pen style.
						 &n_width,     // @pyparm int|width||The pen width.
						 &cr_color))   // @pyparm long|color||The pen color.
		{
		return NULL;
		}
	lp.lopnStyle = n_pen_style;
	lp.lopnWidth.x = n_width;
	lp.lopnWidth.y = 0;
	lp.lopnColor = cr_color;

	HPEN hpen;
	GUI_BGN_SAVE;
	hpen=::CreatePenIndirect (&lp);
	GUI_END_SAVE;

	if(!hpen)RETURN_ERR ("CreatePenIndirect call failed");
	return Py_BuildValue("i",hpen);
	}

// @pymethod <o PyWin32Sdk>|CreateFontIndirect|Creates a font from a dict of font properties and returns its handle.
// Return Values: A handle to the created font 
PyObject *
sdk_create_font_indirect(PyObject *self, PyObject *args)
	{
	// @comm The code for the PyCFont was contributed by Dave Brennan
	// (Last known address is brennan@hal.com, but I hear he is now at Microsoft)
	// args contains a dict of font properties 
	PyObject *font_props; 
                  // properties.  Valid dictionary keys are:<nl> 
                  // name<nl> 
                  // size<nl> 
                  // weight<nl> 
                  // italic<nl> 
                  // underline 
	if (!PyArg_ParseTuple (args, "O", &font_props) ||
		!PyDict_Check (font_props))
		{
		PyErr_Clear();
		RETURN_ERR ("Expected dictionary of font properties.");
		}

	// populate LOGFONT struct with values from dictionary
	LOGFONT lf;
	if (!DictToLogFont(font_props, &lf))
		return NULL;

	HFONT hfont;
    if (!(hfont=::CreateFontIndirect(&lf))) 
		RETURN_ERR ("CreateFontIndirect call failed");

	return Py_BuildValue("i",hfont);
	}

int CALLBACK EnumFontFamiliesExProc(ENUMLOGFONTEX *lpelfe, NEWTEXTMETRICEX *lpntme, int FontType, LPARAM lParam)
	{
	PyObject *d = (PyObject*)lParam;
	PyObject *lfdict = LogFontToDict(lpelfe->elfLogFont);
	PyDict_SetItemString(d, (char*)lpelfe->elfFullName, lfdict);
	Py_XDECREF(lfdict);
    return 1;
	}

// @pymethod <o PyWin32Sdk>|EnumFontFamiliesEx|Enumerates all fonts in the system that match the font characteristics specified by the LOGFONT structure. 
PyObject *
sdk_enum_font_families_ex(PyObject *self, PyObject *args)
	{
	// args contains a dict of font properties 
	PyObject *font_props; 
	if (!PyArg_ParseTuple (args, "O", &font_props) ||
		!PyDict_Check (font_props))
		{
		PyErr_Clear();
		RETURN_ERR ("Expected dictionary of font properties.");
		}
	
	// populate LOGFONT struct with values from dictionary
	LOGFONT lf;
	if (!DictToLogFont(font_props, &lf))
		return NULL;

	// screen dc
	HDC hdc = GetDC(NULL);

	PyObject *d = PyDict_New();
	EnumFontFamiliesEx(
		hdc,              // handle to DC
		&lf,              // font information
		(FONTENUMPROC)EnumFontFamiliesExProc, // callback function
		LPARAM(d),        // additional data
		DWORD(0)          // not used; must be 0
		);
	ReleaseDC(NULL,hdc);
	
	return d;
	}

// @pymethod <o PyWin32Sdk>|GetTextFace|Retrieves the typeface name of the font that is selected into the specified device contextPyObject *
PyObject *
sdk_get_text_face(PyObject *self, PyObject *args)
	{
	HDC hdc = 0;
	if (!PyArg_ParseTuple(args,"|i",&hdc)) return NULL;
	
	// screen dc
	bool releaseDC=false;
	if(!hdc)
		{
		hdc = GetDC(NULL);
		releaseDC=true;
		}
	char faceName[LF_FACESIZE];
	GetTextFace(
		hdc,            // handle to DC
		LF_FACESIZE,    // length of typeface name buffer
		faceName		// typeface name buffer
		);
	if(releaseDC)
		ReleaseDC(NULL,hdc);
	return Py_BuildValue("s",faceName);
	}

  
// @pymethod |PyWin32Sdk|CreateDC|Creates a DC
// Return Values: A handle to the created DC 
PyObject *
sdk_create_dc(PyObject *self, PyObject *args)
	{
	char *psz;
	if (!PyArg_ParseTuple(args,"s",&psz))return NULL;
	GUI_BGN_SAVE;
	HDC hdc=::CreateDC(psz,NULL,NULL,NULL);
	GUI_END_SAVE;
	if(!hdc)RETURN_ERR("CreateDC failed");
	return Py_BuildValue("i",hdc);
	}

// @pymethod |PyWin32Sdk|DeleteObject|Delete a GDI object from its handle
// Return Values: None 
static PyObject *
sdk_delete_object(PyObject *self, PyObject *args)
	{
	HGDIOBJ hobj;  
	if (!PyArg_ParseTuple (args, "i",&hobj))
		return NULL;
	
	if(hobj)
		{
		GUI_BGN_SAVE;
		::DeleteObject(hobj);
		GUI_END_SAVE;
		}

	RETURN_NONE;
	}

// @pymethod |PyWin32Sdk|GetDesktopWindow|Returns the DesktopWindow
// Return Values: The DesktopWindow as a PyCWnd object 
static PyObject *
sdk_get_desktop_window(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,GetDesktopWindow);
	HWND hwnd=::GetDesktopWindow();
	CWnd *pWnd = CWnd::FromHandle(hwnd);
	if (pWnd==NULL)
		RETURN_ERR("The window handle is invalid.");
	return PyCWnd::make( UITypeFromCObject(pWnd), pWnd)->GetGoodRet();
	}

// @pymethod |PyWin32Sdk|GetStockObject|The GetStockObject function retrieves a handle to one of the predefined stock pens, brushes, fonts, or palettes. 
// Return Values: A handle to the type of stock object requested
static PyObject *
sdk_get_stock_object(PyObject *self, PyObject *args)
	{
	int fnObject;   // type of stock object
	if (!PyArg_ParseTuple (args, "i",&fnObject))
		return NULL;

	HGDIOBJ hobj=GetStockObject(fnObject);
	return Py_BuildValue("i",hobj);
	}

// Return Values: the red,green,blue components of a color
static PyObject *
sdk_get_rgb_values(PyObject *self, PyObject *args)
	{
	long clr;   
	if (!PyArg_ParseTuple (args, "l",&clr))
		return NULL;
	return Py_BuildValue("iii",(int)GetRValue(clr),(int)GetGValue(clr),(int)GetBValue(clr));
	}

// @pymethod |PyWin32Sdk|BeginDeferWindowPos|It allocates memory for a multiple-window position structure and returns the handle to the structure
// Return Values: A handle to a DeferWindowPos structure
static PyObject *
sdk_begin_defer_window_pos(PyObject *self, PyObject *args)
	{
	int nNumWindows=0;   
	if (!PyArg_ParseTuple (args, "i",&nNumWindows))
		return NULL;

	GUI_BGN_SAVE;
	HDWP hdwp=BeginDeferWindowPos(nNumWindows);   
	GUI_END_SAVE;

	return Py_BuildValue("l",(long)hdwp);
	}

// @pymethod |PyWin32Sdk|DeferWindowPos|Updates the specified multiple-window position structure for the specified window
// Return Values: A handle to the DeferWindowPos structure
static PyObject *
sdk_defer_window_pos(PyObject *self, PyObject *args)
	{
    HDWP hWinPosInfo;       // handle to internal structure
	HWND hWnd;              // handle to window to position
	HWND hWndInsertAfter;   // placement-order handle
	int x;                  // horizontal position
	int y;                  // vertical position  
	int cx;                 // width
	int cy;                 // height
	UINT uFlags;            // window-positioning flags);
	if (!PyArg_ParseTuple (args, "lll(iiii)i:DeferWindowPos",
		&hWinPosInfo,&hWnd,&hWndInsertAfter,&x,&y,&cx,&cy,&uFlags))
		return NULL;

	GUI_BGN_SAVE;
	HDWP hdwp=DeferWindowPos(hWinPosInfo,hWnd,hWndInsertAfter,
		x,y,cx,cy,uFlags);   
	GUI_END_SAVE;
	return Py_BuildValue("l",hdwp);
	}


// @pymethod |PyWin32Sdk|EndDeferWindowPos|Simultaneously updates the position and size of one or more windows in a single screen-refreshing cycle. 
// Return Values: None
static PyObject *
sdk_end_defer_window_pos(PyObject *self, PyObject *args)
	{
	HDWP hdwp;
	if (!PyArg_ParseTuple (args, "l",&hdwp))
		return NULL;

	GUI_BGN_SAVE;
	BOOL bret=EndDeferWindowPos(hdwp);   
	GUI_END_SAVE;
	if(!bret)
		RETURN_ERR("EndDeferWindowPos failed");

	RETURN_NONE;
	}


// @pymethod |PyWin32Sdk|PostMessage|Posts a message to a window.
// Return Values: Nonzero value if it succeeds
PyObject *
sdk_post_message(PyObject *self, PyObject *args)
{
	HWND hwnd;
	int message;
	int wParam=0;
	int lParam=0;
	if (!PyArg_ParseTuple(args, "iiii:PostMessage",
			  &hwnd,    // @pyparm handle|handle of destination window 
		      &message, // @pyparm int|idMessage||The ID of the message to send.
	          &wParam,  // @pyparm int|wParam||The wParam for the message
	          &lParam)) // @pyparm int|lParam||The lParam for the message

		return NULL;
	long rc;
	GUI_BGN_SAVE;
	// @pyseesdk Win32Sdk|PostMessage
	rc = ::PostMessage(hwnd,message,wParam,lParam);
	GUI_END_SAVE;
	return Py_BuildValue("l",rc);
}

// @pymethod |PyWin32Sdk|SendMessage|Sends a message to a window.
// Return Values: The return value (a long) specifies the result of the message processing and depends on the message sent.
PyObject *
sdk_send_message(PyObject *self, PyObject *args)
	{
	HWND hwnd;
	UINT message;
	WPARAM wParam=0;
	LPARAM lParam=0;
	if (!PyArg_ParseTuple(args, "iiii:SendMessage",
			  &hwnd,    // @pyparm handle|handle of destination window 
		      &message, // @pyparm int|idMessage||The ID of the message to send.
	          &wParam,  // @pyparm int|wParam||The wParam for the message
	          &lParam)) // @pyparm int|lParam||The lParam for the message
		return NULL;
	long rc;
	GUI_BGN_SAVE;
	// @pyseesdk Win32Sdk|SendMessage
	rc = ::SendMessage(hwnd,message,wParam,lParam);
	GUI_END_SAVE;
	return Py_BuildValue("l",rc);
	}

// LPARAM is a string
// @pymethod |PyWin32Sdk|SendMessageLS|Sends a message to a window. A special version for Python with LPARAM as string
// Return Values: The return value (a long) specifies the result of the message processing and depends on the message sent.
PyObject *
sdk_send_message_ls(PyObject *self, PyObject *args)
	{
	HWND hwnd;
	UINT message;
	WPARAM wParam=0;
	LPARAM lParam=0;
	char *sParam;
	if (!PyArg_ParseTuple(args, "iiis:SendMessageLS",
			  &hwnd,    // @pyparm handle|handle of destination window 
		      &message, // @pyparm int|idMessage||The ID of the message to send.
	          &wParam,  // @pyparm int|wParam||The wParam for the message
	          &sParam)) // @pyparm string|lParam||The lParam for the message
		return NULL;
	lParam=(LPARAM)sParam;

	GUI_BGN_SAVE;
	// @pyseesdk Win32Sdk|SendMessage
	long rc = ::SendMessage(hwnd,message,wParam,lParam);
	GUI_END_SAVE;
	return Py_BuildValue("l",rc);
	}

// LPARAM is the len of the string to allocate and return
// @pymethod |PyWin32Sdk|SendMessageRS|Sends a message to a window. A special version for Python that returns a string
// Return Values: A string
PyObject *
sdk_send_message_rs(PyObject *self, PyObject *args)
	{
	HWND hwnd;
	UINT message;
	WPARAM wParam=0;
	LPARAM lParam=0;
	if (!PyArg_ParseTuple(args, "iiii:SendMessageRS",
			  &hwnd,    // @pyparm handle|handle of destination window 
		      &message, // @pyparm int|idMessage||The ID of the message to send.
	          &wParam,  // @pyparm int|wParam||The wParam for the message
	          &lParam)) // @pyparm int|lParam||The lParam for the message
		return NULL;
	
	CString str;
	char *pBuf=str.GetBuffer(lParam+1);
	GUI_BGN_SAVE;
	// @pyseesdk Win32Sdk|SendMessage
	LPARAM rc = ::SendMessage(hwnd,message,wParam,(LPARAM)pBuf);
	GUI_END_SAVE;
	PyObject *strobj= Py_BuildValue("s",pBuf);
	str.ReleaseBuffer();
	return strobj;
	}

// @pymethod |PyWin32Sdk|SendMessageRA|Sends a message to a window. A special version for Python
// Return Values: A tuple (result, wParam, lParam)
PyObject *
sdk_send_message_ra(PyObject *self, PyObject *args)
	{
	HWND hwnd;
	UINT message;
	WPARAM wParam=0;
	LPARAM lParam=0;
	if (!PyArg_ParseTuple(args, "ii|ii:SendMessageRA",
			  &hwnd,    // @pyparm handle|handle of destination window 
		      &message, // @pyparm int|idMessage||The ID of the message to send.
	          &wParam,  // @pyparm int|wParam||The wParam for the message
	          &lParam)) // @pyparm int|lParam||The lParam for the message
		return NULL;
	
	GUI_BGN_SAVE;
	// @pyseesdk Win32Sdk|SendMessage
	LPARAM rc = ::SendMessage(hwnd,message,(WPARAM)&wParam,(LPARAM)&lParam);
	GUI_END_SAVE;
	return Py_BuildValue("iii",rc,wParam,lParam);
	}

// @pymethod |PyWin32Sdk|SendMessageGT|Sends a message to a window. A special version for Python
// Return Values: A tuple of integers
PyObject *
sdk_send_message_gt(PyObject *self, PyObject *args)
	{
	HWND hwnd;
	UINT message;
	WPARAM wParam=256;
	LPARAM lParam=0;
	if (!PyArg_ParseTuple(args, "ii|ii:SendMessageGT",
			  &hwnd,    // @pyparm handle|handle of destination window 
		      &message, // @pyparm int|idMessage||The ID of the message to send.
	          &wParam,  // @pyparm int|wParam||The wParam for the message
	          &lParam)) // @pyparm int|lParam||The lParam for the message
		return NULL;
	
	int *data = new int[wParam];

	GUI_BGN_SAVE;
	// @pyseesdk Win32Sdk|SendMessage
	LPARAM rc = ::SendMessage(hwnd,message,(WPARAM)wParam,(LPARAM)data);
	GUI_END_SAVE;

	PyObject *list = PyList_New(rc);
	for (int i=0;i<rc;i++) 
		PyList_SetItem(list,i,Py_BuildValue("i",data[i]));

	delete[] data;
	return list;
	}

// @pymethod |PyWin32Sdk|SendMessageGL|A special version of send message for Python that returns a string from an edit control 
static PyObject *
sdk_send_message_gl(PyObject *self, PyObject *args)
	{
	HWND hwnd;
	UINT message;
	WPARAM wParam=0;
	LPARAM lParam=0;
	if (!PyArg_ParseTuple(args, "iiii:SendMessageGL",
			  &hwnd,    // @pyparm handle|handle of destination window 
		      &message, // @pyparm int|idMessage||The ID of the message to send.
	          &wParam,  // @pyparm int|wParam||The wParam for the message
	          &lParam)) // @pyparm int|lParam||The lParam for the message
		return NULL;

	const WORD length=256;
	static char buf[length+1];
	memcpy(buf,&length,2);
	GUI_BGN_SAVE;
	LPARAM nc_copy=::SendMessage(hwnd,message,wParam,(LPARAM)buf);
	GUI_END_SAVE;
	buf[nc_copy]='\0';
	PyObject *strobj= Py_BuildValue("s",buf);
	return strobj;
	}

// @pymethod |PyWin32Sdk|SendMessageGetRect|A special version of send message for Python that returns a rectangle 
static PyObject *
sdk_send_message_get_rect(PyObject *self, PyObject *args)
	{
	HWND hwnd;
	UINT message;
	WPARAM wParam;
	LPARAM lParam=0;
	if (!PyArg_ParseTuple(args, "iii|i:SendMessageGetRect",
			  &hwnd,    // @pyparm handle|handle of destination window 
		      &message, // @pyparm int|idMessage||The ID of the message to send.
	          &wParam,  // @pyparm int|wParam||The wParam for the message
	          &lParam)) // @pyparm int|lParam||The lParam for the message
		return NULL;

	RECT rc;
	GUI_BGN_SAVE;
	LPARAM ret = SendMessage(hwnd,message,wParam,(LPARAM)&rc);
	GUI_END_SAVE;
	if(ret==LB_ERR)
		RETURN_ERR("SendMessageGetRect failed");
	
	return Py_BuildValue("iiii",rc.left,rc.top,rc.right,rc.bottom);
	}

// @pymethod |PyWin32Sdk|SendMessageSetRect|A special version of send message for Python with LPARAM a rect 
static PyObject *
sdk_send_message_set_rect(PyObject *self, PyObject *args)
	{
	HWND hwnd;
	UINT message;
	WPARAM wParam;
	RECT rc;
	if (!PyArg_ParseTuple(args, "iii(iiii):SendMessageSetRect",
			  &hwnd,    // @pyparm handle|handle of destination window 
		      &message, // @pyparm int|idMessage||The ID of the message to send.
	          &wParam,  // @pyparm int|wParam||The wParam for the message
	          &rc.left, &rc.top, &rc.right, &rc.bottom)) 
		return NULL;
	GUI_BGN_SAVE;
	LPARAM ret = SendMessage(hwnd,message,wParam,(LPARAM)&rc);
	GUI_END_SAVE;
	return Py_BuildValue("i", ret);
	}

// @pymethod |PyWin32Sdk|SendMessageMS|A special version of send message for Python 
// LPARAM is a tuple representing win32 MSG structure
static PyObject *
sdk_send_message_ms(PyObject *self, PyObject *args)
	{
	// message params
	HWND hwnd;
	UINT message;
	WPARAM wParam;
	
	// LPARAM is a tuple equivalent to a win32 MSG struct
	MSG msg;
	LPARAM lParam;
	if (!PyArg_ParseTuple(args, "iii(iiiiii):SendMessageMS",
			  &hwnd,    // @pyparm handle|handle of destination window 
		      &message, // @pyparm int|idMessage||The ID of the message to send.
	          &wParam,  // @pyparm int|wParam||The wParam for the message
	          &msg.hwnd, &msg.message, &msg.wParam, &msg.lParam, &msg.time, &lParam)) 
		return NULL;
	msg.pt.x= LOWORD(lParam);
	msg.pt.y= HIWORD(lParam);
	lParam = SendMessage(hwnd, message, 0, (LPARAM)&msg);
	GUI_BGN_SAVE;
	LPARAM ret = SendMessage(hwnd, message, wParam, (LPARAM)&msg);
	GUI_END_SAVE;
	return Py_BuildValue("i", lParam);
	}

// @pymethod |PyWin32Sdk|CharFromPos|return the carret pos from a coordinate
static PyObject *
sdk_charfrompos(PyObject *self, PyObject *args)
	{
	HWND hwnd;
	UINT message = EM_CHARFROMPOS;
	WPARAM wParam = 0;
	POINTL point;
	if (!PyArg_ParseTuple(args, "i(ii):CharFromPos",
			  &hwnd,    // @pyparm handle|handle of destination window 
	          &point.x, &point.y)) 
		return NULL;
	GUI_BGN_SAVE;
	LPARAM ret = SendMessage(hwnd,message,wParam,(LPARAM)&point);
	GUI_END_SAVE;
	return Py_BuildValue("i", ret);
	}

// @pymethod |PyWin32Sdk|GetCaretPos|return the carret pos from a coordinate
static PyObject *
sdk_getcaretpos(PyObject *self, PyObject *args)
	{
	POINT point;
	GUI_BGN_SAVE;
	BOOL ret;
	ret = ::GetCaretPos(&point);
	GUI_END_SAVE;
	if (ret)
		return Py_BuildValue("ii",point.x, point.y);
	return NULL;
	}

// @pymethod |PyWin32Sdk|SetCursor|The SetCursor function establishes the cursor shape
// Return Values: A handle to the previous cursor
static PyObject *
sdk_set_cursor(PyObject *self, PyObject *args)
	{
	HCURSOR hCursor;
	if (!PyArg_ParseTuple (args, "l",&hCursor))
		return NULL;

	GUI_BGN_SAVE;
	hCursor=::SetCursor(hCursor);   
	GUI_END_SAVE;
	return Py_BuildValue("l",hCursor);
	}

// @sdkproto HCURSOR LoadCursor(
// HINSTANCE hInstance,  // handle to application instance
// LPCTSTR lpCursorName  // name string or cursor resource identifier);
// @pymethod |PyWin32Sdk|LoadStandardCursor|Loads the specified predefined cursor resource
// Return Values: A handle to the loaded cursor
static PyObject *
sdk_load_standard_cursor(PyObject *self, PyObject *args)
	{
	int id;
	if (!PyArg_ParseTuple (args, "i",&id))
		return NULL;
	GUI_BGN_SAVE;
	HCURSOR hCursor=::LoadCursor(NULL,(LPCTSTR)id); 
	GUI_END_SAVE;
	return Py_BuildValue("l",hCursor);
	}

// @sdkproto int ShowCursor(  
// BOOL bShow   // cursor visibility flag);
// @pymethod |PyWin32Sdk|ShowCursor|Specifies whether the internal display counter is to be incremented or decremented
// Return Values: The return value specifies the new display counter. 
static PyObject *
sdk_show_cursor(PyObject *self,PyObject *args)
	{
	BOOL bShow;
	if (!PyArg_ParseTuple (args, "i",&bShow))
		return NULL;
	GUI_BGN_SAVE;
	int count=::ShowCursor(bShow);
	GUI_END_SAVE;
	return Py_BuildValue("i",count);
	}

// @sdkproto HCURSOR GetCursor(VOID)
// @pymethod |PyWin32Sdk|GetCursor|retrieves the handle to the current cursor
// Return Values:the handle to the current cursor
static PyObject *
sdk_get_cursor(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,GetCursor);
	GUI_BGN_SAVE;
	HCURSOR hCursor=::GetCursor();  
	GUI_END_SAVE;
	return Py_BuildValue("l",hCursor);
	}


// @pymethod |PyWin32Sdk|IsWindow|Determines whether the specified window handle identifies an existing window
static PyObject *
sdk_is_window(PyObject *self, PyObject *args)
	{
	HWND hWnd;
	if (!PyArg_ParseTuple (args, "l",&hWnd))
		return NULL;
	GUI_BGN_SAVE;
	BOOL bAns=::IsWindow(hWnd); 
	GUI_END_SAVE;
	return Py_BuildValue("i",bAns);
	}

// @sdkproto DWORD SetClassLong(  
//	HWND hWnd,       // handle of window
//	int nIndex,      // index of value to change  
//	LONG dwNewLong   // new value);
// @pymethod |PyWin32Sdk|SetClassLong|
// Return Values: The old class long value (style) for the attribute. 
static PyObject *
sdk_set_class_long(PyObject *self, PyObject *args)
	{
	HWND hWnd;
	int nIndex;
	LONG dwNewLong;
	if (!PyArg_ParseTuple (args, "iil",&hWnd,&nIndex,&dwNewLong))
		return NULL;
	GUI_BGN_SAVE;
	DWORD dwOldLong=::SetClassLong(hWnd,nIndex,dwNewLong);
	GUI_END_SAVE;
	return Py_BuildValue("l",dwOldLong);
	}
 
static PyObject *
sdk_set_window_long(PyObject *self, PyObject *args)
	{
	HWND hWnd;
	int nIndex;
	LONG newLong;
	if (!PyArg_ParseTuple (args, "iil",&hWnd,&nIndex,&newLong))
		return NULL;
	GUI_BGN_SAVE;
	LONG oldLong=::SetWindowLong(hWnd,nIndex,newLong);
	GUI_END_SAVE;
	return Py_BuildValue("l",oldLong);
	}

static PyObject *
sdk_get_window_long(PyObject *self, PyObject *args)
	{
	HWND hWnd;
	int nIndex;
	if (!PyArg_ParseTuple (args, "ii",&hWnd,&nIndex))
		return NULL;
	GUI_BGN_SAVE;
	LONG attr=::GetWindowLong(hWnd,nIndex);
	GUI_END_SAVE;
	return Py_BuildValue("l",attr);
	}
 
 // @pymethod |PyWin32Sdk|ShowWindow|sets the specified window's show state
// Return Values: None
static PyObject *
sdk_show_window(PyObject *self, PyObject *args)
	{
	HWND hWnd;
	int nCmdShow;
	if (!PyArg_ParseTuple (args, "ii",&hWnd,&nCmdShow))
		return NULL;
	GUI_BGN_SAVE;
	::ShowWindow(hWnd,nCmdShow);  
	GUI_END_SAVE;
	RETURN_NONE;
	}

 // @pymethod |PyWin32Sdk|DestroyWindow|Destroy window
static PyObject *
sdk_destroy_window(PyObject *self, PyObject *args)
	{
	HWND hWnd;
	if (!PyArg_ParseTuple (args, "i",&hWnd))
		return NULL;
	GUI_BGN_SAVE;
	BOOL res = DestroyWindow(hWnd);  
	GUI_END_SAVE;
	return Py_BuildValue("i",res);
	}

// @sdkproto HWND GetDlgItem(HWND hDlg,int nIDDlgItem);     
// @pymethod |PyWin32Sdk|GetDlgItem|Returns the window handle of the given control
// Return Values: The integer identifier of the control
static PyObject *
sdk_get_dlg_item(PyObject *self, PyObject *args)
	{
	HWND hDlg;
	int nIDDlgItem;
	if (!PyArg_ParseTuple (args, "li",&hDlg,&nIDDlgItem))
		return NULL;
	GUI_BGN_SAVE;
	HWND hControl=::GetDlgItem(hDlg,nIDDlgItem);
	GUI_END_SAVE;
	return Py_BuildValue("i",hControl);
	}


// @sdkproto BOOL EnableWindow(HWND hWnd,BOOL bEnable);     
// @pymethod |PyWin32Sdk|EnableWindow|enables or disables mouse and keyboard input to the specified window or control
// Return Values: If the window was previously disabled, the return value is nonzero.
static PyObject *
sdk_enable_window(PyObject *self, PyObject *args)
	{
	HWND hWnd;
	BOOL bEnable;
	if (!PyArg_ParseTuple (args, "li",&hWnd,&bEnable))
		return NULL;
	GUI_BGN_SAVE;
	BOOL ret =::EnableWindow(hWnd,bEnable);
	GUI_END_SAVE;
	return Py_BuildValue("i",ret);
	}


// @sdkproto HWND CreateWindowEx(  DWORD dwExStyle,      // extended window style
// @sdkproto   LPCTSTR lpClassName,  // pointer to registered class name
// @sdkproto   LPCTSTR lpWindowName, // pointer to window name
// @sdkproto   DWORD dwStyle,        // window style
// @sdkproto   int x,                // horizontal position of window
// @sdkproto   int y,                // vertical position of window
// @sdkproto   int nWidth,           // window width  
// @sdkproto   int nHeight,          // window height
// @sdkproto   HWND hWndParent,      // handle to parent or owner window
// @sdkproto   HMENU hMenu,          // handle to menu, or child-window identifier
// @sdkproto   HINSTANCE hInstance,  // handle to application instance
// @sdkproto   LPVOID lpParam        // pointer to window-creation data);
// @pymethod |PyWin32Sdk|CreateWindowEx|Creates an overlapped, pop-up, or child window with an extended style
static PyObject *
sdk_create_window_ex(PyObject *self, PyObject *args)
	{
	CREATESTRUCT cs;
	cs.lpCreateParams=NULL;
	if (!PyArg_ParseTuple(args, "iszi(iiii)ii|i:CreateWindowEx",
	          &cs.dwExStyle, // @pyparm int|styleEx||The extended style of the window being created.
	          &cs.lpszClass,   // @pyparm string|classId||The class ID for the window.  May not be None.
	          &cs.lpszName, // @pyparm string|windowName||The title for the window, or None
			  &cs.style, // @pyparm int|style||The style for the window.
			  &cs.x,&cs.y,&cs.cx,&cs.cy,
			  // @pyparm (x, y, w, h)|rect||The size and position of the window.
			  &cs.hwndParent, // @pyparm HWND|hParent||The handle of the parent window of the new window..
			  &cs.hMenu, // @pyparm int|id or handle||Identifies a menu or a child-window identifier 
			  &cs.lpCreateParams)) // @pyparm long|lpCreateParams||A pointer CreateParams (as cs.lpCreateParams)
			  return NULL;
	cs.hInstance = AfxGetInstanceHandle();

	GUI_BGN_SAVE;
	HWND hWnd = ::CreateWindowEx(cs.dwExStyle, cs.lpszClass,
			cs.lpszName, cs.style, cs.x, cs.y, cs.cx, cs.cy,
			cs.hwndParent, cs.hMenu, cs.hInstance, cs.lpCreateParams);
	GUI_END_SAVE;
	if (!hWnd)RETURN_ERR("Win32Sdk::CreateWindowEx failed");
	return Py_BuildValue("i",hWnd);
	}

// @pymethod (left, top, right, bottom)|PyWin32Sdk|GetWindowRect|Returns the screen coordinates of the windows upper left corner
static PyObject *
sdk_get_window_rect(PyObject *self, PyObject *args)
{
	HWND hWnd;
	if (!PyArg_ParseTuple (args, "l",&hWnd))
		return NULL;
	RECT rect;
	GUI_BGN_SAVE;
	::GetWindowRect(hWnd,&rect);
	GUI_END_SAVE;
	// @pyseesdk GetWindowRect
	return Py_BuildValue("(iiii)",rect.left, rect.top, rect.right, rect.bottom);
}

// @sdkproto     
// @pymethod |PyWin32Sdk|SetWindowPos|Sets the windows position information
static PyObject *
sdk_set_window_pos(PyObject *self, PyObject *args)
{
	HWND hWnd;
	HWND insertAfter;
	int x,y,cx,cy;
	int flags;
    // @pyparm int|hWnd||The hwnd to set its position
    // @pyparm int|hWndInsertAfter||A hwnd, else one of the win32con.HWND_* constants.
	// @pyparm (x,y,cx,cy)|position||The new position of the window.
	// @pyparm int|flags||Window positioning flags.
	if (!PyArg_ParseTuple(args,"ii(iiii)i:SetWindowPos",&hWnd,
		        (int *)(&insertAfter), &x, &y, &cx, &cy, &flags ))
		return NULL;
	GUI_BGN_SAVE;
	// @pyseesdk SetWindowPos
	::SetWindowPos(hWnd, insertAfter, x, y, cx, cy, flags);
	GUI_END_SAVE;
	RETURN_NONE;
}

// @sdkproto     
// @pymethod |PyWin32Sdk|MoveWindow|Moves the windows
static PyObject *
sdk_move_window(PyObject *self, PyObject *args)
{
	HWND hWnd;
	int x,y,cx,cy;
	BOOL bRepaint = TRUE;
    // @pyparm int|hWnd||The hwnd to set its position
	// @pyparm (x,y,cx,cy)|position||The new position of the window.
	// @pyparm int|bRepaint||Repaint flag
	if (!PyArg_ParseTuple(args,"i(iiii)|i:MoveWindow",&hWnd,
		        &x, &y, &cx, &cy, &bRepaint ))
		return NULL;
	GUI_BGN_SAVE;
	// @pyseesdk MoveWindow
	MoveWindow(hWnd, x, y, cx, cy, bRepaint);
	GUI_END_SAVE;
	RETURN_NONE;
}

// @sdkproto BOOL IntersectRect(LPRECT lprcDst,CONST RECT *lprcSrc1,CONST RECT *lprcSrc2)  
// @pymethod |PyWin32Sdk|IntersectRect|Calculates the intersection of two source rectangles 
static PyObject *
sdk_intersect_rect(PyObject *self, PyObject *args)
	{
	RECT rcSrc1,rcSrc2;
	if (!PyArg_ParseTuple(args,"(iiii)(iiii):IntersectRect",
		        &rcSrc1.left, &rcSrc1.top, &rcSrc1.right,&rcSrc1.bottom,
				&rcSrc2.left, &rcSrc2.top, &rcSrc2.right,&rcSrc2.bottom
				))
		return NULL;
	RECT rcDst;
	BOOL inrersect=::IntersectRect(&rcDst,&rcSrc1,&rcSrc2);
	return Py_BuildValue("(iiii)i",rcDst.left,rcDst.top,rcDst.right,rcDst.bottom,inrersect);
	}

// @sdkproto BOOL UnionRect(LPRECT lprcDst,CONST RECT *lprcSrc1,CONST RECT *lprcSrc2)  
// @pymethod |PyWin32Sdk|UnionRect|Calculates the intersection of two source rectangles 
static PyObject *
sdk_union_rect(PyObject *self, PyObject *args)
	{
	RECT rcSrc1,rcSrc2;
	if (!PyArg_ParseTuple(args,"(iiii)(iiii):IntersectRect",
		        &rcSrc1.left, &rcSrc1.top, &rcSrc1.right,&rcSrc1.bottom,
				&rcSrc2.left, &rcSrc2.top, &rcSrc2.right,&rcSrc2.bottom
				))
		return NULL;
	RECT rcDst;
	BOOL notempty = ::UnionRect(&rcDst,&rcSrc1,&rcSrc2);
	return Py_BuildValue("(iiii)i",rcDst.left,rcDst.top,rcDst.right,rcDst.bottom, notempty);
	}

// @sdkproto DWORD GetTickCount(VOID)
// @pymethod |PyWin32Sdk|GetTickCount|Retrieves the number of milliseconds that have elapsed since the system was started
static PyObject *
sdk_get_tick_count(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,GetCursor);
	GUI_BGN_SAVE;
	DWORD ticks=::GetTickCount();
	GUI_END_SAVE;
	return Py_BuildValue("l",ticks);
	}

/////////////////////////////////////////
// crack NMHDR information about a notification message.
// field0: hwndFrom Window handle to the control sending a message. 
// field1: idFrom Identifier of the control sending a message. 
// field2: code Notification code. This member can be a control-specific notification code or it can be one of the common notification codes. 	
// @pymethod |PyWin32Sdk|CrackNMHDR
static PyObject *
sdk_crack_nmhdr(PyObject *self, PyObject *args)
	{
	NMHDR *pHdr;
	if (!PyArg_ParseTuple (args, "l",&pHdr))
		return NULL;
	if (pHdr==NULL) RETURN_ERR("Invalid pointer to NMHDR structure");
	return Py_BuildValue("iii", pHdr->hwndFrom, pHdr->idFrom, pHdr->code);
	}
static PyObject *
sdk_parse_drawitemstruct(PyObject *self, PyObject *args)
	{
	LPDRAWITEMSTRUCT pDS;
	if (!PyArg_ParseTuple (args, "l",&pDS))
		return NULL;
	if (pDS==NULL) RETURN_ERR("Invalid pointer to DRAWITEMSTRUCT");
	return Py_BuildValue("i",pDS->hDC);	
	}

// General helpers
// newalloc will be moved to win32struct
// extern creators in win32util
TCITEM* New_TCITEM(PyObject *args)
	{
	if (!PyTuple_Check(args))
		RETURN_TYPE_ERR("TCITEM must be a tuple");
	int len = PyTuple_Size(args);
	if(len!=4)
		RETURN_ERR("TCITEM must be a tuple of len 4");
	TCITEM *p=new TCITEM;
	memset(p,0,sizeof(TCITEM));
	p->mask = PyInt_AsLong(PyTuple_GET_ITEM(args, 0));
	p->iImage = PyInt_AsLong(PyTuple_GET_ITEM(args, 1));
	p->lParam = PyInt_AsLong(PyTuple_GET_ITEM(args, 2));
	p->pszText = PyString_AsString(PyTuple_GET_ITEM(args, 3));
	return p;
	}

static void* newalloc(char *strid,PyObject *fields)
	{
	CString str(strid);
	if(str=="TCITEM")
		return New_TCITEM(fields);
	return 0;
	}
static PyObject *
sdk_new(PyObject *self, PyObject *args)
	{
	char *strid;
	PyObject *fields;
	if (!PyArg_ParseTuple (args,"sO:New",&strid,&fields))
		return NULL;
	return Py_BuildValue("l",newalloc(strid,fields));
	}

static PyObject *
sdk_delete(PyObject *self, PyObject *args)
	{
	void *p;
	if (!PyArg_ParseTuple (args,"l:Delete",&p))
		return NULL;
	if(p) delete p;
	RETURN_NONE;
	}

//////////////////////////////////////////
static PyObject *
sdk_get_current_directory(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,GetCurrentDirectory);
	char szPath[MAX_PATH];
	GUI_BGN_SAVE;
	DWORD nr=::GetCurrentDirectory(MAX_PATH,szPath);
	GUI_END_SAVE;
	if (nr==0) RETURN_ERR("GetCurrentDirectory failed");
	return Py_BuildValue("s",szPath);
	}
static PyObject *
sdk_set_current_directory(PyObject *self, PyObject *args)
	{
	char *pszPath;
	if (!PyArg_ParseTuple (args, "s:SetCurrentDirectory",&pszPath))
		return NULL;
	BOOL res;
	GUI_BGN_SAVE;
	res=::SetCurrentDirectory(pszPath);
	GUI_END_SAVE;
	return Py_BuildValue("i",res);
	}

// NOTE: Always returns the same types even on errors (see different approach in win32api)
//       In case of error, the message is shown to the user through a message box
// @pymethod int|PyWin32Sdk|ShellExecute|Opens, edits or prints a file.
static PyObject *
sdk_shell_execute( PyObject *self, PyObject *args )
	{
	HWND hwnd;
	char *op, *file, *params, *dir;
	int show;
	if (!PyArg_ParseTuple(args, "izszzi:ShellExecute", 
		      &hwnd, // @pyparm int|hwnd||The handle of the parent window.  This window receives any message boxes an application produces (for example, for error reporting).
		      &op,   // @pyparm string|op||The operation to perform.  May be "open", "print", or None, which defaults to "open".
		      &file, // @pyparm string|file||The name of the file to open.
		      &params,// @pyparm string|params||The parameters to pass, if the file name contains an executable.  Should be None for a document file.
		      &dir,  // @pyparm string|dir||The initial directory for the application.
		      &show))// @pyparm int|bShow||Specifies whether the application is shown when it is opened. If the lpszFile parameter specifies a document file, this parameter is zero.
		return NULL;
	if (dir==NULL)
		dir="";
	GUI_BGN_SAVE;
	HINSTANCE rc=::ShellExecute(hwnd, op, file, params, dir, show);
	GUI_END_SAVE;
	// @pyseeapi ShellExecute
	char szMsg[512]="OK";
	if ((rc) <= (HINSTANCE)32) 
		{
		BOOL bHaveMessage = ::FormatMessage(FORMAT_MESSAGE_FROM_SYSTEM, NULL,(DWORD)rc, 0, szMsg,sizeof(szMsg), NULL )>0;
		if (!bHaveMessage)
			lstrcpy(szMsg,"Error. No error message is available");
		}
	return Py_BuildValue("is",rc,szMsg);
	// @rdesc The instance handle of the application that was run. (This handle could also be the handle of a dynamic data exchange [DDE] server application.)
	// If there is an error, the method raises an exception.
	}

/////////////////////// 
// New

// @pymethod |PyWin32Sdk|DragQueryPoint|Retrieves the position of the mouse pointer at the time a file was dropped during a drag-and-drop operation. 
static PyObject *
sdk_drag_query_point( PyObject *self, PyObject *args )
{
	HDROP hDrop;
	// @pyparm int|hDrop||Handle identifying the structure containing the file names.
	if (!PyArg_ParseTuple(args, "i:DragQueryPoint", &hDrop))
		return NULL;
	POINT pt;
	GUI_BGN_SAVE;
	BOOL ret=::DragQueryPoint(hDrop,&pt); // @pyseeapi DragQueryPoint
	GUI_END_SAVE;
	return Py_BuildValue("i(ii)",ret,pt.x,pt.y);
}

// @pymethod |PyWin32Sdk|IsClipboardFormatAvailable|Determines whether the clipboard contains data in the specified format. 
static PyObject *
sdk_is_clipboard_format_available(PyObject *self, PyObject *args)
{
	// @pyparm int|format||Specifies a standard or registered clipboard format.
	UINT format;   
	if (!PyArg_ParseTuple (args, "i",&format))
		return NULL;
	GUI_BGN_SAVE;
	BOOL ret=::IsClipboardFormatAvailable(format); // @pyseeapi IsClipboardFormatAvailable
	GUI_END_SAVE;
	return Py_BuildValue("i",ret);
}

// @pymethod |PyWin32Sdk|GetClipboardTextData|GetClipboardData in CF_TEXT format
static PyObject *
sdk_get_clipboard_text_data(PyObject *self, PyObject *args) 
	{
	HWND hWndNewOwner=NULL;
	if (!PyArg_ParseTuple (args, "|i",&hWndNewOwner))
		return NULL;
	::OpenClipboard(hWndNewOwner);
	HANDLE hClipMem=::GetClipboardData(CF_TEXT);
	if(!hClipMem) 
		{
		::CloseClipboard();
		return Py_BuildValue("s","");
		}
	LPSTR lpClipMem=(LPSTR)GlobalLock(hClipMem);
	CString str(lpClipMem);
	::GlobalUnlock(lpClipMem);
	::CloseClipboard();
	return Py_BuildValue("s",(LPCTSTR)str);
	}

//////////////////////////////////
// Copy/Paste support
static CLIPFORMAT cfFileName=NULL;

static PyObject*
sdk_is_clipboard_file_data_available(PyObject *self, PyObject *args) 
	{
	CHECK_NO_ARGS2(args,IsClipboardFileDataAvailable);
	if(!cfFileName)cfFileName = ::RegisterClipboardFormat(_T("FileName"));
	COleDataObject dataObject;
	if(!dataObject.AttachClipboard())
		return Py_BuildValue("i",0);
	HGLOBAL hObjDesc = dataObject.GetGlobalData(cfFileName);
	if(!hObjDesc)
		return Py_BuildValue("i",0);
	return Py_BuildValue("i",1);
	}

static PyObject*
sdk_get_clipboard_file_data(PyObject *self, PyObject *args) 
	{
	CHECK_NO_ARGS2(args,GetClipboardFileData);
	if(!cfFileName)cfFileName = ::RegisterClipboardFormat(_T("FileName"));
	COleDataObject dataObject;
	if(!dataObject.AttachClipboard())
		return Py_BuildValue("s","");
	HGLOBAL hObjDesc = dataObject.GetGlobalData(cfFileName);
	if(!hObjDesc)
		return Py_BuildValue("s","");
	LPSTR lpClipMem=(LPSTR)GlobalLock(hObjDesc);
	CString str(lpClipMem);
	::GlobalUnlock(lpClipMem);
	return Py_BuildValue("s",(LPCTSTR)str);
	}

static PyObject *
sdk_register_clipboard_format(PyObject *self, PyObject *args)
{
	char *pszFmt=NULL; // private clipboard string format 
	if (!PyArg_ParseTuple(args,"s:RegisterClipboardFormat",&pszFmt))
		return NULL;

	CLIPFORMAT cfPrivate=CF_TEXT;
	if(pszFmt && lstrlen(pszFmt))
		{
		cfPrivate = ::RegisterClipboardFormat(_T(pszFmt));
		if(!cfPrivate) RETURN_ERR("RegisterClipboardFormat failed");
		}
	return Py_BuildValue("i", cfPrivate);
}



static PyObject*
sdk_get_dialog_base_units(PyObject *self, PyObject *args) 
	{
	CHECK_NO_ARGS2(args,GetDialogBaseUnits);
	LONG l=GetDialogBaseUnits();
	return Py_BuildValue("(i,i)", LOWORD(l), HIWORD(l));
	}


static PyObject*
sdk_get_focus(PyObject *self, PyObject *args) 
	{
	CHECK_NO_ARGS2(args,GetFocus);
	HWND hWnd=GetFocus();
	return Py_BuildValue("i", hWnd);
	}

static PyObject*
sdk_co_initialize(PyObject *self, PyObject *args) 
	{
	CHECK_NO_ARGS2(args,CoInitialize);
	HRESULT hr=CoInitialize(NULL);
	return Py_BuildValue("i",hr);
	}
static PyObject*
sdk_co_uninitialize(PyObject *self, PyObject *args) 
	{
	CHECK_NO_ARGS2(args,CoUninitialize);
	CoUninitialize();
	RETURN_NONE;
	}

static PyObject*
sdk_map_virtual_key(PyObject *self, PyObject *args) 
	{
	UINT uCode,uMapType;
	if(!PyArg_ParseTuple (args, "ii",&uCode,&uMapType))
		return NULL;
	UINT ret=MapVirtualKey(uCode,uMapType);
	return Py_BuildValue("i",ret);
	}

static PyObject*
GetWMString(PyObject *self, PyObject *args)
	{
	int pval;
	if (!PyArg_ParseTuple(args, "i", &pval))
		return NULL;
	char *buf = (char*)pval;
	PyObject *obj = Py_BuildValue("s",buf);
//	delete[] buf;
	return obj;
	}

// InitCommonControlsEx
static PyObject*
sdk_init_common_controls_ex(PyObject *self, PyObject *args) 
	{
 	if (!PyArg_ParseTuple(args, ""))
		return NULL;
    INITCOMMONCONTROLSEX which; 
    which.dwICC = ICC_WIN95_CLASSES;
    which.dwSize = sizeof(INITCOMMONCONTROLSEX);
    InitCommonControlsEx(&which);
	RETURN_NONE;
	}

///////////////////////////
// Tooltip support 
// (normally should be PyObject, but...)

static TOOLINFO*
fillToolInfo(TOOLINFO *pti, HWND hwnd, WPARAM uId, RECT *prc=NULL, LPTSTR lpszText=NULL, UINT uFlags=0)
	{
    TOOLINFO& ti = *pti;
	memset(&ti, 0, sizeof(TOOLINFO));
	ti.cbSize = sizeof(TOOLINFO);
    ti.uFlags = uFlags;
    ti.hwnd = hwnd;
    ti.hinst = 0;
    ti.uId = uId;
    ti.lpszText = lpszText;
	if(prc){
		ti.rect.left = prc->left;    
		ti.rect.top = prc->top;
		ti.rect.right = prc->right;
		ti.rect.bottom = prc->bottom;
		}
	return pti;
	}

// NewToolInfo (intil we make TOOLINFO a PyObject)
static PyObject*
sdk_new_tool_info(PyObject *self, PyObject *args)
	{
	HWND hwnd;
	int id;
	RECT rc = {0, 0, 0, 0};
	if (!PyArg_ParseTuple(args,"ii|(iiii):NewToolInfo", &hwnd, &id,
		        &rc.left, &rc.top, &rc.right,&rc.bottom))
		return NULL;
	TOOLINFO *pti = new TOOLINFO;
	if(rc.left == rc.right &&  rc.top==rc.bottom && rc.left==0 && rc.top==0)
		fillToolInfo(pti, hwnd, id);
	else
		fillToolInfo(pti, hwnd, id, &rc);
	return Py_BuildValue("i", int(pti));
	}

// DelToolInfo (intil we make TOOLINFO a PyObject)
static PyObject*
sdk_del_tool_info(PyObject *self, PyObject *args)
	{
	int pti;
	if (!PyArg_ParseTuple(args,"i:DelToolInfo", &pti))
		return NULL;
	delete ((TOOLINFO*)pti);
	RETURN_NONE;
	}

// AddTool
static PyObject*
sdk_add_tool(PyObject *self, PyObject *args)
	{
	HWND hwnd, hwndParent;
	int id;
	RECT rc;
	char *pszText=NULL;
	if (!PyArg_ParseTuple(args,"iii(iiii)|s:AddTool", &hwnd, &hwndParent, &id,
		        &rc.left, &rc.top, &rc.right,&rc.bottom, &pszText))
		return NULL;
	char *buf = pszText;
	if(pszText!=NULL)
		{
		buf = new char[256]; // assert big enough for reuse
		strncpy(buf, pszText, min(256, strlen(pszText)+1));
		buf[255]='\0';
		}
	TOOLINFO ti;
	SendMessage(hwnd, TTM_ADDTOOL, 0, (LPARAM)fillToolInfo(&ti, hwndParent, id, &rc, buf));	
	return Py_BuildValue("i", int(buf));
	}

// DeleteTool
static PyObject*
sdk_del_tool(PyObject *self, PyObject *args)
	{
	HWND hwnd, hwndParent;
	int id;
	char *pszText=NULL;
	if (!PyArg_ParseTuple(args,"iii:DeleteTool", &hwnd, &hwndParent, &id))
		return NULL;
	TOOLINFO ti;
 	SendMessage(hwnd, TTM_DELTOOL, 0, (LPARAM)fillToolInfo(&ti, hwndParent, id));	
	RETURN_NONE;
	}

// NewToolRect
static PyObject*
sdk_new_tool_rect(PyObject *self, PyObject *args)
	{
	HWND hwnd, hwndParent;
	int id;
	RECT rc;
	if (!PyArg_ParseTuple(args,"iii(iiii):NewToolInfo", &hwnd, &hwndParent, &id,
		        &rc.left, &rc.top, &rc.right,&rc.bottom))
		return NULL;
	TOOLINFO ti;
	SendMessage(hwnd, TTM_NEWTOOLRECT,0 , (LPARAM)fillToolInfo(&ti, hwndParent, id, &rc));	
	RETURN_NONE;
	}

// UpdateTipText
static PyObject*
sdk_update_tip_text(PyObject *self, PyObject *args)
	{
	HWND hwnd, hwndParent;
	int id;
	char *pszText;
	int pval;
	if (!PyArg_ParseTuple(args,"iiisi:UpdateTipText", &hwnd, &hwndParent, &id,
		        &pszText, &pval))
		return NULL;
	
	char *buf = (char*)pval;
	strncpy(buf, pszText, min(256, strlen(pszText)+1));
	buf[255]='\0';

	TOOLINFO ti;
	SendMessage(hwnd, TTM_UPDATETIPTEXT,0 , (LPARAM)fillToolInfo(&ti, hwndParent, id, NULL, buf));	
	return Py_BuildValue("i", int(buf));
	}


 // @object PyWin32Sdk|A module wrapper object.  It is a general utility object, and is not associated with an MFC object.
BEGIN_PYMETHODDEF(Win32Sdk)
	{"CreatePen",sdk_create_pen,	1},		// @pymeth CreatePen|Creates a pen and returns its handle
	{"CreateBrush",sdk_create_brush,	1}, // @pymeth CreateBrush|Creates a brush and returns its handle.
	{"CreateFontIndirect",sdk_create_font_indirect,	1}, // @pymeth|CreateFontIndirect|Creates a font from a dict of font properties and returns its handle.
	{"EnumFontFamiliesEx",sdk_enum_font_families_ex,	1}, // @pymeth|EnumFontFamiliesEx|Enumerates all fonts in the system that match the font characteristics specified by the LOGFONT structure.
	{"GetTextFace",sdk_get_text_face,	1}, // @pymeth|GetTextFace|Retrieves the typeface name of the font that is selected into the specified device contextPyObject *
	{"CreateDC",sdk_create_dc,	1}, // @pymeth|CreateDC|Creates a DC.
	{"DeleteObject",sdk_delete_object,	1}, // @pymeth DeleteObject|Deletes a GDI object from its handle
	{"GetDesktopWindow",sdk_get_desktop_window,	1}, // @pymeth GetDesktopWindow|Returns the DesktopWindow
	{"GetStockObject",sdk_get_stock_object,	1}, // @pymeth GetStockObject|Retrieves a handle to one of the predefined stock pens, brushes, fonts, or palettes.
	{"GetRGBValues",sdk_get_rgb_values,	1}, // @pymeth GetRGBValues|Retuen RGB components
	{"BeginDeferWindowPos",sdk_begin_defer_window_pos,1}, // @pymeth BeginDeferWindowPos|allocates memory for a multiple-window position structure and returns the handle to the structure
	{"EndDeferWindowPos",sdk_end_defer_window_pos,	1}, // @pymeth EndDeferWindowPos|Simultaneously updates the position and size of one or more windows in a single screen-refreshing cycle.
	{"DeferWindowPos",sdk_defer_window_pos,	1}, // @pymeth DeferWindowPos|Updates the specified multiple-window position structure for the specified window	
	{"PostMessage",sdk_post_message,1}, // @pymeth PostMessage|Posts a message to a window.	
	
	{"SendMessage",sdk_send_message,1}, // @pymeth SendMessage|Sends a message to a window.	
	{"SendMessageLS",sdk_send_message_ls,1}, // @pymeth SendMessage|Sends a message to a window. The LPARAM is a string	
	{"SendMessageRS",sdk_send_message_rs,1}, // @pymeth SendMessage|Sends a message to a window. The return value is a string	
	{"SendMessageRA",sdk_send_message_ra,1}, // @pymeth SendMessage|Sends a message to a window. The return value is a tuple	
	{"SendMessageGL",sdk_send_message_gl,1}, // @pymeth SendMessageGL|Sends a message to an edit control. The return value is a string	
	{"SendMessageGT",sdk_send_message_gt,1}, // @pymeth SendMessageGT|	
	{"SendMessageGetRect",sdk_send_message_get_rect,1},// @pymeth SendMessageGetRect|A special version of send message for Python that returns a rectangle 
	{"SendMessageSetRect",sdk_send_message_get_rect,1},// @pymeth SendMessageSetRect|A special version of send message for Python that sets a rectangle 
	{"SendMessageMS",sdk_send_message_ms,1}, // @pymeth SendMessageMS|A special version of send message for Python. LPARAM is a tuple equivalent to a win32 MSG struct

	
	{"SetCursor",sdk_set_cursor,1}, // @pymeth SetCursor|Establishes a cursor shape.	
	{"LoadStandardCursor",sdk_load_standard_cursor,1}, // @pymeth LoadStdCursor|Loads the specified predefined cursor resource.	
	{"ShowCursor",sdk_show_cursor,1}, // @pymeth ShowCursor|Specifies whether the internal display counter is to be incremented or decremented
	{"GetCursor",sdk_get_cursor,1}, // @pymeth ShowCursor|Retrieves the handle to the current cursor	
	{"IsWindow",sdk_is_window,1}, // @pymeth IsWindow|determines whether the specified window handle identifies an existing window.	
	{"GetDlgItem",sdk_get_dlg_item,1}, // @pymeth GetDlgItem|Returns the window handle of the given control.	
	{"EnableWindow",sdk_enable_window,1}, // @pymeth GetDlgItem|enables or disables mouse and keyboard input to the specified window or control
	{"CreateWindowEx",sdk_create_window_ex,1}, // @pymeth CreateWindowEx|Creates an overlapped, pop-up, or child window with an extended style
	{"SetWindowPos",sdk_set_window_pos,1}, // @pymeth SetWindowPos|Sets the windows position information.
	{"MoveWindow",sdk_move_window,1}, // @pymeth MoveWindow|Move window.
	{"GetWindowRect",sdk_get_window_rect,1}, // @pymeth GetWindowRect|Get the windows rectangle.
	{"ShowWindow",sdk_show_window,1}, // @pymeth ShowWindow|sets the specified window's show state
	{"DestroyWindow",sdk_destroy_window,1}, // @pymeth DestroyWindow|Destroy the specified window
	{"SetClassLong",sdk_set_class_long,1}, // @pymeth SetClassLong|
	{"SetWindowLong",sdk_set_window_long,1}, 
	{"GetWindowLong",sdk_get_window_long,1}, 

	{"GetTickCount",sdk_get_tick_count,1}, // @pymeth GetTickCount|Retrieves the number of milliseconds that have elapsed since the system was started

	{"IntersectRect",sdk_intersect_rect,1}, // @pymeth IntersectRect|Calculates the intersection of two source rectangles
	{"UnionRect",sdk_union_rect,1}, // @pymeth UnionRect|Calculates the union of two rectangles

	{"GetCurrentDirectory",sdk_get_current_directory,1}, 
	{"SetCurrentDirectory",sdk_set_current_directory,1}, 
	{"ShellExecute",sdk_shell_execute,1}, 

	{"DragQueryPoint",sdk_drag_query_point,1}, // @pymeth DragQueryPoint|Retrieves the position of the mouse pointer at the time a file was dropped during a drag-and-drop operation.
	{"IsClipboardFormatAvailable",sdk_is_clipboard_format_available,1}, // @pymeth IsClipboardFormatAvailable|Determines whether the clipboard contains data in the specified format. 
	{"GetClipboardTextData",sdk_get_clipboard_text_data,1}, // @pymeth GetClipboardTextData|GetClipboardData in CF_TEXT format
	{"IsClipboardFileDataAvailable",sdk_is_clipboard_file_data_available,1}, 
	{"GetClipboardFileData",sdk_get_clipboard_file_data,1}, 
	{"RegisterClipboardFormat",sdk_register_clipboard_format,1}, 

	{"GetDialogBaseUnits",sdk_get_dialog_base_units,1}, 
	{"GetFocus",sdk_get_focus,1}, 
	{"CoInitialize",sdk_co_initialize,1}, 
	{"CoUninitialize",sdk_co_uninitialize,1}, 
	{"MapVirtualKey",sdk_map_virtual_key,1},
	
	{"InitCommonControlsEx",sdk_init_common_controls_ex,1},

	// Tooltips support
	{"NewToolInfo",sdk_new_tool_info,1},
	{"DelToolInfo",sdk_del_tool_info,1},
	{"AddTool",sdk_add_tool,1},
	{"DelTool",sdk_del_tool,1},
	{"NewToolRect",sdk_new_tool_rect,1},
	{"UpdateTipText",sdk_update_tip_text,1},

	// Rich edit support
	{"CharFromPos", sdk_charfrompos, 1},// @pymethod |PyWin32Sdk|CharFromPos|return the carret pos from a coordinate
	{"GetCaretPos", sdk_getcaretpos, 1},// @pymethod |PyWin32Sdk|GetCaretPos|return the current caret position

	///////////////////////////////////////////////////// Temporary
	{"ParseDrawItemStruct",sdk_parse_drawitemstruct,1},// undocumented!
	{"CrackNMHDR",sdk_crack_nmhdr,1}, // undocumented!
	{"New",sdk_new,1}, // undocumented!
	{"Delete",sdk_delete,1}, // undocumented!
	{"GetWMString",GetWMString,1}, // undocumented!

END_PYMETHODDEF()

DEFINE_PYMODULETYPE("PyWin32Sdk",Win32Sdk);


