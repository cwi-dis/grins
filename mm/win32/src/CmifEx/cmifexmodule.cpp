
#define LSIZE	10
#include "cmifex.h"
#include "ezfont.h"

static PyObject *CmifExError;
char cmifClass[100]="";
char dbgmess[100]="";


WNDPROC	orgProc;

typedef enum { ARROW, WAIT, HAND, START } Cursors;
PyIMPORT CWnd *GetWndPtr(PyObject *);

HDC hdc=NULL;
PAINTSTRUCT ps;
static int nPaint=0;

#ifdef __cplusplus
extern "C" {
#endif

//int PyErr_Print (void);
void CmifExErrorFunc(char *str);


LRESULT CALLBACK MyWndProc (HWND hwnd, UINT iMsg, WPARAM wParam, LPARAM lParam)
{

	switch (iMsg)
	{
		case WM_CLOSE:
			ShowWindow(hwnd, SW_HIDE);
			//MessageBox(hwnd, "Window Hidden", "Test", MB_OK);
			return 0;	
	}
	return CallWindowProc(orgProc, hwnd, iMsg, wParam, lParam) ;
}

static PyObject* py_cmifex_CreateWindow(PyObject *self, PyObject *args)
{
	char *wndName;
	PyObject *testOb = Py_None;
	CWnd *newWnd, *mainWnd;
	PyCWnd *testWnd;
	int x=100, y=100, nWidth=200, nHeight=200, visible;
	DWORD ws_style, ws_flags;
	
	newWnd = new CWnd;

	if(!PyArg_ParseTuple(args, "siiiii", &wndName, &x, &y, &nWidth, &nHeight, &visible))
	{
		CmifExErrorFunc("CreateWindow(Title, left, top, right, bottom, visible)");
		Py_INCREF(Py_None);
		return Py_None;
	}


	TRACE("%s, X: %d, Y: %d, W: %d, H: %d\n", wndName, x, y, nWidth, nHeight );
	
	mainWnd = AfxGetMainWnd();

	if(visible)
		ws_flags = WS_OVERLAPPEDWINDOW | WS_VISIBLE | WS_CLIPCHILDREN;  
	else
		ws_flags = WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN;  
	
	if(cmifClass[0]==0)
		strcpy(cmifClass, AfxRegisterWndClass( CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS, LoadCursor (AfxGetInstanceHandle(), IDC_ARROW), (HBRUSH) GetStockObject (WHITE_BRUSH), LoadIcon(NULL, MAKEINTRESOURCE(IDR_PYTHON))));

	if(newWnd->CreateEx(WS_EX_CLIENTEDGE,
						cmifClass, wndName,
						ws_flags,
						x, y, nWidth, nHeight,
						//NULL,
						mainWnd->m_hWnd,
						NULL))
		TRACE("CmifEx CreateWindow OK!\n");
	else
	{
		TRACE("CmifEx CreateWindow FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	

	orgProc = (WNDPROC)SetWindowLong(newWnd->m_hWnd, GWL_WNDPROC, (LONG)MyWndProc);
	
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	testOb = testWnd->GetGoodRet();

	return Py_BuildValue("O", testOb);
} //static PyObject* py_cmifex_CreateWindow(PyObject *self, PyObject *args)

static PyObject* py_cmifex_CreateChildWindow(PyObject *self, PyObject *args)
{
	char *wndName;
	PyObject *testOb = Py_None, *ob = Py_None;
	CWnd *newWnd, *parentWnd;
	PyCWnd *testWnd;
	int x=150, y=150, nWidth=100, nHeight=100;
	
	if(!PyArg_ParseTuple(args, "sOiiii", &wndName, &ob, &x, &y, &nWidth, &nHeight))
	{
		Py_INCREF(Py_None);
		CmifExErrorFunc("CreateChildWindow(Title, Parent, left, top, right, bottom)");
		return Py_None;
	}

	newWnd = new CWnd;
	parentWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, Name: %s, X: %d, Y: %d, W: %d, H: %d\n", parentWnd->m_hWnd, wndName, x, y, nWidth, nHeight );
		
	if(newWnd->CreateEx(WS_EX_CONTROLPARENT, // | WS_EX_CLIENTEDGE,
						cmifClass, wndName,
						WS_CHILD|WS_CLIPSIBLINGS, // | WS_VISIBLE,
						x, y, nWidth, nHeight,
						parentWnd->m_hWnd,
						NULL))
		TRACE("CmifEx CreateChildWindow OK!\n");
	else 
	{
		TRACE("CmifEx CreateChildWindow FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	testOb = testWnd->GetGoodRet();

	return Py_BuildValue("O", testOb);
} //static PyObject* py_cmifex_CreateChildWindow(PyObject *self, PyObject *args)

static PyObject* py_cmifex_ResizeChildWindow(PyObject *self, PyObject *args)
{	
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	WINDOWPLACEMENT newpl;
	char str[100];
		
	if(!PyArg_ParseTuple(args, "O(ii(ii)(ii)(iiii))",
							&ob,
							&newpl.flags, &newpl.showCmd, 
							&newpl.ptMinPosition.x, &newpl.ptMinPosition.y,
							&newpl.ptMaxPosition.x, &newpl.ptMaxPosition.y,
							&newpl.rcNormalPosition.left, &newpl.rcNormalPosition.top, 
							&newpl.rcNormalPosition.right, &newpl.rcNormalPosition.bottom))
		return Py_BuildValue("i", 0);

	hCWnd = GetWndPtr( ob );

	//sprintf(str, "Flags: %d, Cmd: %d", newpl.flags, newpl.showCmd);
	//hCWnd->MessageBox(str, "Placement", MB_OK);

	newpl.length = sizeof(WINDOWPLACEMENT);	
	if(hCWnd->SetWindowPlacement(&newpl))
		return Py_BuildValue("i", 1);
	else
		return Py_BuildValue("i", 0);
} //static PyObject* py_cmifex_ResizeChildWindow(PyObject *self, PyObject *args)	

static PyObject* py_cmifex_ResizeAllChilds(PyObject *self, PyObject *args)
{	
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	int x, y, xClient, yClient;
	char str[100];

	if(!PyArg_ParseTuple(args, "Oiiii", &ob, &x, &y, &xClient, &yClient))
	{
		Py_INCREF(Py_None);
		CmifExErrorFunc("ResizeAllChilds( Parent, width, height, oldWidth, oldHeight)");
		return Py_None;
	}

	hCWnd = GetWndPtr( ob );

	MyCascadeChildWindows(hCWnd->m_hWnd, x, y, xClient, yClient);

	return Py_BuildValue("i", 1);	
} //static PyObject* py_cmifex_ResizeAllChilds(PyObject *self, PyObject *args)	

static PyObject* py_cmifex_BeginPaint(PyObject *self, PyObject *args)
{	
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	int index;
	

	if(!PyArg_ParseTuple(args, "Oi", &ob, &index))
		return Py_BuildValue("i", 0);

	if(nPaint)
		return Py_BuildValue("i", 1);	

	hCWnd = GetWndPtr( ob );	
	if((hdc = BeginPaint(hCWnd->m_hWnd, &ps))==NULL)
		return Py_BuildValue("i", 0);

	nPaint = 1;
	
	//TRACE("Begin Paint!\n");

	return Py_BuildValue("i", 1);
} //static PyObject* py_cmifex_BeginPaint(PyObject *self, PyObject *args)		

static PyObject* py_cmifex_EndPaint(PyObject *self, PyObject *args)
{	
	int index;	
	CWnd *hCWnd;
	PyObject *ob = Py_None;
		
	if(!PyArg_ParseTuple(args, "Oi", &ob, &index))
		return Py_BuildValue("i", 0);

	if(!nPaint)
		return Py_BuildValue("i", 1);

	hCWnd = GetWndPtr( ob );	
	EndPaint(hCWnd->m_hWnd, &ps);
	nPaint=0;

	//TRACE("End Paint!\n");

	return Py_BuildValue("i", 1);
} //static PyObject* py_cmifex_EndPaint(PyObject *self, PyObject *args)

static PyObject* py_cmifex_SetBGColor(PyObject *self, PyObject *args)
{	
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	HWND hWnd;
	HBRUSH      hBrush ;
	HDC         hdc ;
	RECT        rc ;
	UWORD r, g, b;
	
	if(!PyArg_ParseTuple(args, "Oiii", &ob, &r, &g, &b))
	{
		CmifExErrorFunc("SetBGColor(Window, r, g, b)");
		return Py_BuildValue("i", 0);
	}

	hCWnd = GetWndPtr( ob );
		
	hWnd = hCWnd->m_hWnd;

	GetClientRect (hWnd, &rc) ;
	hdc = GetDC (hWnd) ;
	hBrush = CreateSolidBrush(RGB(r, g, b)) ;
	FillRect (hdc, &rc, hBrush) ;
	ReleaseDC (hWnd, hdc) ;
	DeleteObject (hBrush) ;

	return Py_BuildValue("i", 1);
} //static PyObject* py_cmifex_SetBGColor(PyObject *self, PyObject *args)


static PyObject* py_cmifex_ValidateRect(PyObject *self, PyObject *args)
{	
	int index;	
	CWnd *hCWnd;
	PyObject *ob = Py_None;
	RECT rect;
	char str[100];
	
	if(!PyArg_ParseTuple(args, "O(iiii)", &ob, &rect.left, &rect.top, &rect.right, &rect.bottom))
		return Py_BuildValue("i", 0);

	hCWnd = GetWndPtr( ob );	

	wsprintf(str, "L:: %d, T: %d, R: %d, B: %d", rect.left, rect.top, rect.right, rect.bottom);
	MessageBox( hCWnd->m_hWnd, str, "Debug", MB_OK);

	ValidateRect(hCWnd->m_hWnd, &rect);

	return Py_BuildValue("i", 1);
} //static PyObject* py_cmifex_ValidateRect(PyObject *self, PyObject *args)

static PyObject* py_cmifex_DrawLine(PyObject *self, PyObject *args)
{
	HDC hdc;
	HWND hWnd;
	int nDPI=0;
		
	if(!PyArg_ParseTuple(args, ""))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}

	return Py_BuildValue("i", nDPI);
} //

static PyObject* py_cmifex_DrawRectangle(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	HDC hdc=NULL;
	HBRUSH hBrush;
	HWND hWnd;
	RECT rect;
	BOOL res;
	int top, left, right, bottom;
	int r, g, b;

	if(!PyArg_ParseTuple(args, "O(iiii)(iii)",
							&ob, &left, &top, &right, &bottom, &r, &g, &b))
	{
		CmifExErrorFunc("DrawRectangle(hWindow, rect, color)");
		Py_INCREF(Py_None);
		return Py_None;
	}

	rect.left = left;
	rect.top = top;
	rect.right = right;
	rect.bottom = bottom;

	hCWnd = GetWndPtr( ob );	
	if((hdc = GetDC(hCWnd->m_hWnd))==NULL)
		MessageBox(hCWnd->m_hWnd, "NULL HDC!", "Debug", MB_ICONSTOP|MB_OK);	

	if((hBrush = CreateSolidBrush (RGB(r, g, b)))==NULL)
		MessageBox(hCWnd->m_hWnd, "NULL BRUSH!", "Debug", MB_ICONSTOP|MB_OK);	

	if((res = FrameRect(hdc, &rect, hBrush))==FALSE)
		MessageBox(hCWnd->m_hWnd, "FrameRect Error!", "Debug", MB_ICONSTOP|MB_OK);
	ReleaseDC(hCWnd->m_hWnd, hdc);
	DeleteObject(hBrush);

	return Py_BuildValue("i", res);
} //static PyObject* py_cmifex_DrawRectangle(PyObject *self, PyObject *args)

static PyObject* py_cmifex_DrawString(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	HDC hdc=NULL;
	HWND hWnd;
	BOOL res;
	HBRUSH hBrush ;
    RECT   rect ;
	char *string;
	int top, left;
	int r, g, b;
	static int times=1;

	if(!PyArg_ParseTuple(args, "O(iis)",
							&ob, &left, &top, &string))
	{
		CmifExErrorFunc("(hWindow, (x, y, string))");
		Py_INCREF(Py_None);
		return Py_None;
	}

	hCWnd = GetWndPtr( ob );	
	if((hdc = GetDC(hCWnd->m_hWnd))==NULL)
		MessageBox(hCWnd->m_hWnd, "NULL HDC!", "Debug", MB_ICONSTOP|MB_OK);	
	
	TextOut(hdc, left, top, string, strlen(string));

	ReleaseDC(hCWnd->m_hWnd, hdc);
	
	return Py_BuildValue("i", res);
} //static PyObject* py_cmifex_DrawString(PyObject *self, PyObject *args)

static PyObject* py_cmifex_FillRectangle(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	HDC hdc=NULL;
	HWND hWnd;
	BOOL res;
	HBRUSH hBrush ;
    RECT   rect ;
	int top, left, right, bottom;
	int r, g, b;
	static int times=1;

	if(!PyArg_ParseTuple(args, "O(iiii)(iii)",
							&ob, &left, &top, &right, &bottom, &r, &g, &b))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}

	rect.left = left;
	rect.top = top;
	rect.right = right;
	rect.bottom = bottom;

	hCWnd = GetWndPtr( ob );	
	if((hdc = GetDC(hCWnd->m_hWnd))==NULL)
		MessageBox(hCWnd->m_hWnd, "NULL HDC!", "Debug", MB_ICONSTOP|MB_OK);	
	
	if((hBrush = CreateSolidBrush (RGB(r, g, b)))==NULL)
		MessageBox(hCWnd->m_hWnd, "NULL BRUSH!", "Debug", MB_ICONSTOP|MB_OK);	

	FillRect(hdc, &rect, hBrush) ;
	ReleaseDC(hCWnd->m_hWnd, hdc);
	DeleteObject (hBrush) ;

	return Py_BuildValue("i", res);
} //static PyObject* py_cmifex_FillRectangle(PyObject *self, PyObject *args)

static PyObject* py_cmifex_DrawFontString(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	HFONT hfont, g;
	char *facename;
	char *str;
	int size, xPos, yPos;
		
	if(!PyArg_ParseTuple(args, "Osi(iis)", &ob, &facename, &size, &xPos, &yPos, &str))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}
		
	hCWnd = GetWndPtr( ob );	
	if((hdc = GetDC(hCWnd->m_hWnd))==NULL)
		MessageBox(hCWnd->m_hWnd, "NULL HDC!", "Debug", MB_ICONSTOP|MB_OK);	

	hfont = EzCreateFont(hdc, facename, size*10, 0, 0, TRUE);
	SelectObject(hdc, hfont);
	TextOut(hdc, xPos, yPos, str, size*10);
	DeleteObject(SelectObject(hdc, GetStockObject(SYSTEM_FONT)));
	ReleaseDC(hCWnd->m_hWnd, hdc);

	return Py_BuildValue("l", hfont);
} //static PyObject* py_cmifex_DrawFontString(PyObject *self, PyObject *args)

static PyObject* py_cmifex_GetTextMetrics(PyObject *self, PyObject *args)
{
	HDC hdc;
	HWND hWnd;
	TEXTMETRIC tm;
	
	if(!PyArg_ParseTuple(args, ""))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}

	hWnd = GetActiveWindow();
	hdc = GetDC(hWnd);
	GetTextMetrics(hdc, &tm);
	ReleaseDC(hWnd, hdc);
	
	return Py_BuildValue("lll", tm.tmHeight, tm.tmAscent, tm.tmMaxCharWidth);
} //static PyObject* py_cmifex_GetTextMetrics(PyObject *self, PyObject *args)

static PyObject* py_cmifex_GetTextWidth(PyObject *self, PyObject *args)
{
	HDC hdc;
	HWND hWnd;
	char *str;
	SIZE strSize;
	TEXTMETRIC tm;
	
	if(!PyArg_ParseTuple(args, "s", &str))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}

	hWnd = GetActiveWindow();
	hdc = GetDC(hWnd);
	if(!GetTextExtentPoint32(hdc, str, strlen(str), &strSize))
		MessageBox(hWnd, "GetTextExtentPoint32 Error!", "Debug", MB_OK);
	ReleaseDC(hWnd, hdc);
	
	return Py_BuildValue("i", strSize.cy);
} //static PyObject* py_cmifex_GetTextWidth(PyObject *self, PyObject *args)

static PyObject* py_cmifex_GetScreenWidth(PyObject *self, PyObject *args)
{
	HDC hdc;
	HWND hWnd;
	int nWidth=0;
	
	if(!PyArg_ParseTuple(args, ""))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}

	hWnd = GetActiveWindow();
	hdc = GetDC(hWnd);
	nWidth = GetDeviceCaps(hdc, HORZRES);
	ReleaseDC(hWnd, hdc);
	
	return Py_BuildValue("i", nWidth);
} //static PyObject* py_cmifex_GetScreenWidth(PyObject *self, PyObject *args)

static PyObject* py_cmifex_GetScreenHeight(PyObject *self, PyObject *args)
{
	HDC hdc;
	HWND hWnd;
	int nHeight=0;
	
	if(!PyArg_ParseTuple(args, ""))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}

	hWnd = GetActiveWindow();
	hdc = GetDC(hWnd);
	nHeight = GetDeviceCaps(hdc, VERTRES);
	ReleaseDC(hWnd, hdc);
	
	return Py_BuildValue("i", nHeight);
} //static PyObject* py_cmifex_GetScreenHeight(PyObject *self, PyObject *args)

static PyObject* py_cmifex_GetScreenXDPI(PyObject *self, PyObject *args)
{
	HDC hdc;
	HWND hWnd;
	int nDPI=0;
	
	if(!PyArg_ParseTuple(args, ""))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}

	hWnd = GetActiveWindow();
	hdc = GetDC(hWnd);
	nDPI = GetDeviceCaps(hdc, LOGPIXELSX);
	ReleaseDC(hWnd, hdc);

	return Py_BuildValue("i", nDPI);
} //static PyObject* py_cmifex_GetScreenXDPI(PyObject *self, PyObject *args)

static PyObject* py_cmifex_GetScreenYDPI(PyObject *self, PyObject *args)
{
	HDC hdc;
	HWND hWnd;
	int nDPI=0;
		
	if(!PyArg_ParseTuple(args, ""))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}

	hWnd = GetActiveWindow();
	hdc = GetDC(hWnd);
	nDPI = GetDeviceCaps(hdc, LOGPIXELSY);
	ReleaseDC(hWnd, hdc);

	return Py_BuildValue("i", nDPI);
} //static PyObject* py_cmifex_GetScreenYDPI(PyObject *self, PyObject *args)

static PyObject* py_cmifex_SetCursor(PyObject *self, PyObject *args)
{
	HINSTANCE hInst;
	HCURSOR hPCursor, hNCursor;
	Cursors nCursor;
	int ret=0;

	if(!PyArg_ParseTuple(args, "i", &nCursor))
	{
		CmifExErrorFunc("SetCursor(CursorID))");
		Py_INCREF(Py_None);
		return Py_None;
	}
	
	switch(nCursor)
	{
		case ARROW:
			hNCursor = LoadCursor(NULL, IDC_ARROW);			
			break;				

		case HAND:
			hInst = AfxGetInstanceHandle();
			hNCursor = LoadCursor(hInst, MAKEINTRESOURCE(IDC_POINT_HAND));			
			break;	

		case WAIT:
			hNCursor = LoadCursor(NULL, IDC_WAIT);			
			break;
			
		case START:
			hNCursor = LoadCursor(NULL, IDC_APPSTARTING);			
	}

	hPCursor = SetCursor(hNCursor);
	
	return Py_BuildValue("l", hPCursor);
} //static PyObject* py_cmifex_SetCursor(PyObject *self, PyObject *args)

static PyObject* py_cmifex_ScreenToBox(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	RECT rect, box;
	POINT pt;
	BOOL fIn;
	
	if(!PyArg_ParseTuple(args, "O(ii)(iiii)", &ob, &pt.x, &pt.y, &box.left, &box.top, &box.right, &box.bottom))
	{
		CmifExErrorFunc("ScreenToBox(Window, (xPos, yPos), (left, top, right, bottom))");
		Py_INCREF(Py_None);
		return Py_None;
	}
	hCWnd = GetWndPtr( ob );
	hCWnd->ScreenToClient(&pt);
	fIn = PtInRect(&box, pt);
		
	return Py_BuildValue("i", fIn);
} //static PyObject* py_cmifex_ScreenToBox(PyObject *self, PyObject *args)

static PyObject* py_cmifex_ScreenToClient(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	POINT pt;
	BOOL fIn;
	
	char str[50];

	if(!PyArg_ParseTuple(args, "Oii", &ob, &pt.x, &pt.y))
	{
		CmifExErrorFunc("ScreenToClient(Window, (xPos, yPos))");
		Py_INCREF(Py_None);
		return Py_None;
	}
	hCWnd = GetWndPtr( ob );
	hCWnd->ScreenToClient(&pt);
	return Py_BuildValue("ii", pt.x, pt.y);
} //static PyObject* py_cmifex_ScreenToClient(PyObject *self, PyObject *args)

static PyMethodDef CmifExMethods[] = 
{
	//Window Functions
	{ "CreateWindow", py_cmifex_CreateWindow, 1 },
	{ "CreateChildWindow", py_cmifex_CreateChildWindow, 1 },
	{ "ResizeChildWindow", py_cmifex_ResizeChildWindow, 1 },
	{ "ResizeAllChilds", py_cmifex_ResizeAllChilds, 1 },

	//Drawing Funtions
	{ "DrawString", py_cmifex_DrawString, 1 },
	{ "DrawFontString", py_cmifex_DrawFontString, 1 },
	{ "DrawLine", py_cmifex_DrawLine, 1 },
	{ "DrawRectangle", py_cmifex_DrawRectangle, 1 },
	{ "FillRectangle", py_cmifex_FillRectangle, 1 },
	{ "ValidateRect", py_cmifex_ValidateRect, 1 },
	{ "SetBGColor", py_cmifex_SetBGColor, 1 },
	{ "BeginPaint", py_cmifex_BeginPaint, 1 },
	{ "EndPaint", py_cmifex_EndPaint, 1 },
	
	//Get... Funtions
	{ "GetTextMetrics", py_cmifex_GetTextMetrics, 1 },
	{ "GetScreenWidth", py_cmifex_GetScreenWidth, 1 },
	{ "GetScreenHeight", py_cmifex_GetScreenHeight, 1 },
	{ "GetScreenXDPI", py_cmifex_GetScreenXDPI, 1 },
	{ "GetScreenYDPI", py_cmifex_GetScreenYDPI, 1 },

	//Set... Functions
	{ "SetCursor", py_cmifex_SetCursor, 1 },

	//Utilities 
	{ "ScreenToBox", py_cmifex_ScreenToBox, 1 },
	{ "ScreenToClient", py_cmifex_ScreenToClient, 1 },

	{ NULL, NULL }
};

PyEXPORT 
void initcmifex()
{
	PyObject *m, *d;
	m = Py_InitModule("cmifex", CmifExMethods);
	d = PyModule_GetDict(m);
	CmifExError = PyString_FromString("cmifex.error");
	PyDict_SetItemString(d, "error", CmifExError);
}

void CmifExErrorFunc(char *str)
{
	PyErr_SetString (CmifExError, str);
	PyErr_Print();
}

#ifdef __cplusplus
}
#endif
