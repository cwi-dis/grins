#include "Python.h"
#include "stdafx.h"
#include "win32ui.h"
#include "win32assoc.h"
#include "win32cmd.h"
#include "win32win.h"

#include "ezfont.h"
#include <string.h>
#include <math.h>

#include "resource.h"
#include "cmifexhelp.h"

#define PyIMPORT  __declspec(dllimport)
#define PyEXPORT  __declspec(dllexport)
#define LSIZE	10

#ifdef __cplusplus
extern "C" {
#endif

static PyObject *CmifExError;
char cmifClass[100]="";
char dbgmess[100]="";

WNDPROC		orgProc;
BOOL flg=FALSE;

typedef enum { ARROW, WAIT, HAND, START, G_HAND, U_STRECH,
			   D_STRECH, L_STRECH, R_STRECH, UL_STRECH, 
			   UR_STRECH, DR_STRECH, DL_STRECH, PUT} Cursors;
//PyIMPORT CWnd *GetWndPtr(PyObject *);

HDC hdc=NULL;
PAINTSTRUCT ps;
static int nPaint=0;


//int PyErr_Print (void);
void CmifExErrorFunc(char *str);



LRESULT CALLBACK MyWndProc (HWND hwnd, UINT iMsg, WPARAM wParam, LPARAM lParam)
{

	switch (iMsg)
	{
		case WM_CLOSE:
			if (!flg)
			{
				ShowWindow(hwnd, SW_HIDE);
			}
			//flg = FALSE;
			//MessageBox(hwnd, "Window Hidden", "Test", MB_OK);
			return 0;	
		case WM_DESTROY:
			if (!flg)
			{
				return CallWindowProc(orgProc, hwnd, iMsg, wParam, lParam) ;
			}
			//flg = FALSE;
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
	DWORD ws_flags;
	
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
		ws_flags = WS_OVERLAPPEDWINDOW | WS_VISIBLE | WS_CLIPCHILDREN | WS_HSCROLL | WS_VSCROLL;  
	else
		ws_flags = WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN | WS_HSCROLL | WS_VSCROLL;  
	
	if(cmifClass[0]==0)
		strcpy(cmifClass, AfxRegisterWndClass(CS_DBLCLKS, LoadCursor (AfxGetInstanceHandle(), IDC_ARROW), (HBRUSH) GetStockObject (WHITE_BRUSH), LoadIcon(NULL, MAKEINTRESOURCE(IDR_PYTHON))));
		//strcpy(cmifClass, AfxRegisterWndClass( CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS, LoadCursor (AfxGetInstanceHandle(), IDC_ARROW), (HBRUSH) GetStockObject (WHITE_BRUSH), LoadIcon(NULL, MAKEINTRESOURCE(IDR_PYTHON))));

	if(newWnd->CreateEx(WS_EX_CLIENTEDGE,
						cmifClass, wndName,
						ws_flags,
						x, y, nWidth, nHeight,
						NULL,
						/*mainWnd->m_hWnd,*/
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



static PyObject* py_example_SetFlag(PyObject *self, PyObject *args)
{
	int x;
			
	if(!PyArg_ParseTuple(args, "i", &x))
	{
		Py_INCREF(Py_None);
		CmifExErrorFunc("SetFlag(flag)");
		return Py_None;
	}

	if (x==1)
		flg = TRUE;
	else flg = FALSE;

	Py_INCREF(Py_None);
	return Py_None;
}



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

	RECT& r=ps.rcPaint;
	nPaint = 1;
	
	
	return Py_BuildValue("(iiii)",r.left,r.top,r.right,r.bottom);
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
	int r, g, b;
	
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
	
	DeleteObject((HBRUSH)
		SetClassLong(hCWnd->m_hWnd, GCL_HBRBACKGROUND,
				   (LONG) hBrush));
	
	//hCWnd->InvalidateRect(NULL,FALSE);
	//hCWnd->UpdateWindow();
	
	FillRect (hdc, &rc, hBrush) ;
	ReleaseDC (hWnd, hdc) ;
	DeleteObject (hBrush) ;

	return Py_BuildValue("i", 1);
} //static PyObject* py_cmifex_SetBGColor(PyObject *self, PyObject *args)


static PyObject* py_cmifex_ValidateRect(PyObject *self, PyObject *args)
{	
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
	int nDPI=0;
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	HDC hdc=NULL;
	HPEN hPen;
	BOOL res;
	int r, g, b, destx, desty, sourx, soury;
	POINT oldpoint;

		
	if(!PyArg_ParseTuple(args, "O(iiii)(iii)", &ob, &sourx, &soury, &destx, &desty, &r, &g, &b))
	{
		CmifExErrorFunc("DrawLine(hWindow, (dx, dy, sx, sy), color)");
		Py_INCREF(Py_None);
		return Py_None;
	}


	hCWnd = GetWndPtr( ob );	
	if((hdc = GetDC(hCWnd->m_hWnd))==NULL)
		MessageBox(hCWnd->m_hWnd, "NULL HDC!", "Debug", MB_ICONSTOP|MB_OK);	

	if((hPen = (HPEN)SelectObject(hdc, CreatePen(PS_SOLID, 0, RGB(r, g, b))))==NULL)
		CmifExErrorFunc("DrawLine: NULL PEN!");

	if((res = MoveToEx(hdc, sourx, soury, &oldpoint))==FALSE)
		MessageBox(hCWnd->m_hWnd, "DrawLine Error! \nCan not move to source \nposition ", 
				   "Debug", MB_ICONSTOP|MB_OK);

	if((res = LineTo(hdc, destx, desty))==FALSE)
		MessageBox(hCWnd->m_hWnd, "DrawLine Error! \nCan not move to source \nposition ", 
				   "Debug", MB_ICONSTOP|MB_OK);
	
	DeleteObject ((HPEN)SelectObject(hdc, hPen)) ;
	ReleaseDC(hCWnd->m_hWnd, hdc);
	DeleteObject(hPen);

	//return Py_BuildValue("i", nDPI);
	return Py_BuildValue("i", res);
} // static PyObject* py_cmifex_DrawLine(PyObject *self, PyObject *args)

static PyObject* py_cmifex_DrawRectangle(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	HDC hdc=NULL;
	HBRUSH hBrush;
	HPEN hPen, oPen;
	RECT rect;
	BOOL res;
	int top, left, right, bottom;
	int r, g, b;
	char* style;
	CString st;

	if(!PyArg_ParseTuple(args, "O(iiii)(iii)s",
							&ob, &left, &top, &right, &bottom, &r, &g, &b, &style))
	{
		CmifExErrorFunc("DrawRectangle(hWindow, rect, color, style)");
		Py_INCREF(Py_None);
		return Py_None;
	}

	st = style;
	rect.left = left;
	rect.top = top;
	rect.right = right;
	rect.bottom = bottom;

	hCWnd = GetWndPtr( ob );	
	if((hdc = GetDC(hCWnd->m_hWnd))==NULL)
		MessageBox(hCWnd->m_hWnd, "NULL HDC!", "Debug", MB_ICONSTOP|MB_OK);	

	if((hBrush = CreateSolidBrush (RGB(r, g, b)))==NULL)
		MessageBox(hCWnd->m_hWnd, "NULL BRUSH!", "Debug", MB_ICONSTOP|MB_OK);
	
	if (st == "d")
	{
		if((hPen = CreatePen (PS_DOT, 0, RGB(0, 0, 0)))==NULL)
			MessageBox(hCWnd->m_hWnd, "NULL PEN!", "Debug", MB_ICONSTOP|MB_OK);

		oPen = (HPEN)SelectObject(hdc,hPen);
	}

	if (st == "d")
	{
		MoveToEx(hdc,rect.left,rect.top,NULL);
		LineTo(hdc,rect.right,rect.top);
		MoveToEx(hdc,rect.right,rect.top,NULL);
		LineTo(hdc,rect.right,rect.bottom);
		MoveToEx(hdc,rect.right,rect.bottom,NULL);
		LineTo(hdc,rect.left,rect.bottom);
		MoveToEx(hdc,rect.left,rect.bottom,NULL);
		LineTo(hdc,rect.left,rect.top);
	}
	else
		if((res = FrameRect(hdc, &rect, hBrush))==FALSE)
			MessageBox(hCWnd->m_hWnd, "FrameRect Error!", "Debug", MB_ICONSTOP|MB_OK);
	
	if (st == "d") DeleteObject(SelectObject(hdc,oPen));
	DeleteObject(hBrush);
	ReleaseDC(hCWnd->m_hWnd, hdc);

	return Py_BuildValue("i", res);
} //static PyObject* py_cmifex_DrawRectangle(PyObject *self, PyObject *args)

static PyObject* py_cmifex_DrawString(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	HDC hdc=NULL;
	BOOL res;
	char *string;
	int top, left;
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


int
checkshortlist( int width, PyObject *list, long **parray, int *pnitems)
{
	int i, n;
	if (!PyList_Check(list)) {
		PyErr_SetString(PyExc_TypeError, "list of tuples expected");
		return 0;
	}
	n = PyList_Size(list);
	*pnitems = n;
	*parray = PyMem_NEW(long, n*width);
	if (*parray == NULL) {
		PyErr_NoMemory();
		return 0;
	}
	for (i = 0; i < n; i++) {
		PyObject *item = PyList_GetItem(list, i);
		int j;
		if (!PyTuple_Check(item) || PyTuple_Size(item) != width) {
			char buf[100];
			PyMem_DEL(*parray);
			sprintf(buf, "list of %d-tuples expected", width);
			PyErr_SetString(PyExc_TypeError, buf);
			return 0;
		}
		for (j = 0; j < width; j++) {
			PyObject *elem = PyTuple_GetItem(item, j);
			if (!PyInt_Check(elem)) {
				PyMem_DEL(*parray);
				PyErr_SetString(PyExc_TypeError,
					   "list of tuples of ints expected");
				return 0;
			}
			(*parray)[i*width+j] = PyInt_AsLong(elem);
		}
	}
	return 1;
}

static PyObject* py_cmifex_FillPolygon(PyObject *self, PyObject *args)
{
	PyObject *list=Py_None, *ob=Py_None;
	long *pts_list; 
	POINT *pts;
	CWnd *hCWnd;
	HDC hdc=NULL;
	BOOL res;
	HBRUSH hBrush ;
	HPEN hPen;
	int r, g, b, npts_list, polyMode, i;
	static int times=1;

	if (!PyArg_ParseTuple(args, "OO(iii)", &ob, &list,  &r, &g, &b))
	{
		CmifExErrorFunc("FillPolygon(Wnd, List, (R, G, B))");
		Py_INCREF(Py_None);
		return Py_None;
	}

	if (!checkshortlist(2, list, (long**)&pts_list, &npts_list))
		if (!PyErr_Occurred())
			PyErr_SetString(PyExc_TypeError, "list should be Point[]");

	if((pts = (POINT*)malloc(npts_list*sizeof(POINT)))==NULL)
	{
		CmifExErrorFunc("FillPolygon: Not Enough Memory!");
		Py_INCREF(Py_None);
		return Py_None;
	}

	for(i=0; i<npts_list; i++)
	{
		pts[i].x = pts_list[i*2];
		pts[i].y = pts_list[i*2+1];
	}

	hCWnd = GetWndPtr( ob );	
	if((hdc = GetDC(hCWnd->m_hWnd))==NULL)
		CmifExErrorFunc("FillPolygon: NULL HDC!");
	
	if((hBrush = (HBRUSH)SelectObject(hdc, CreateSolidBrush (RGB(r, g, b))))==NULL)
		CmifExErrorFunc("FillPolygon: NULL BRUSH!");

	if((hPen = (HPEN)SelectObject(hdc, CreatePen(PS_SOLID, 0, RGB(r, g, b))))==NULL)
		CmifExErrorFunc("FillPolygon: NULL PEN!");

	polyMode = SetPolyFillMode(hdc, WINDING);
	Polygon(hdc, pts, npts_list);
	polyMode = SetPolyFillMode(hdc, polyMode);

	free(pts);

	DeleteObject ((HBRUSH)SelectObject(hdc, hBrush)) ;
	DeleteObject ((HPEN)SelectObject(hdc, hPen)) ;
	ReleaseDC(hCWnd->m_hWnd, hdc);
	
	return Py_BuildValue("i", res);
} //static PyObject* py_cmifex_FillPolygon(PyObject *self, PyObject *args)


static PyObject* py_cmifex_DrawLines(PyObject *self, PyObject *args)
{
	PyObject *list=Py_None, *ob=Py_None;
	long *pts_list; 
	POINT *pts;
	CWnd *hCWnd;
	HDC hdc=NULL;
	BOOL res;
	HPEN hPen;
	int r, g, b, npts_list, i;
	static int times=1;

	if (!PyArg_ParseTuple(args, "OO(iii)", &ob, &list,  &r, &g, &b))
	{
		CmifExErrorFunc("DrawLines(Wnd, List, (R, G, B))");
		Py_INCREF(Py_None);
		return Py_None;
	}

	if (!checkshortlist(2, list, (long**)&pts_list, &npts_list))
		if (!PyErr_Occurred())
			PyErr_SetString(PyExc_TypeError, "list should be Point[]");

	if((pts = (POINT*)malloc(npts_list*sizeof(POINT)))==NULL)
	{
		CmifExErrorFunc("DrawLines: Not Enough Memory!");
		Py_INCREF(Py_None);
		return Py_None;
	}

	for(i=0; i<npts_list; i++)
	{
		pts[i].x = pts_list[i*2];
		pts[i].y = pts_list[i*2+1];
	}

	hCWnd = GetWndPtr( ob );	
	if((hdc = GetDC(hCWnd->m_hWnd))==NULL)
		CmifExErrorFunc("DrawLines: NULL HDC!");
	
	if((hPen = (HPEN)SelectObject(hdc, CreatePen(PS_SOLID, 0, RGB(r, g, b))))==NULL)
		CmifExErrorFunc("DrawLines: NULL PEN!");

	Polyline(hdc, pts, npts_list);

	free(pts);

	DeleteObject ((HPEN)SelectObject(hdc, hPen)) ;
	ReleaseDC(hCWnd->m_hWnd, hdc);
	
	return Py_BuildValue("i", res);
} //static PyObject* py_cmifex_DrawLines(PyObject *self, PyObject *args)


static PyObject* py_cmifex_FillRectangle(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	HDC hdc=NULL;
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
	HFONT hfont;
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
	
	return Py_BuildValue("llll", tm.tmHeight, tm.tmAscent, tm.tmMaxCharWidth, tm.tmAveCharWidth);
} //static PyObject* py_cmifex_GetTextMetrics(PyObject *self, PyObject *args)

static PyObject* py_cmifex_GetTextWidth(PyObject *self, PyObject *args)
{
	HDC hdc;
	HWND hWnd;
	char *str;
	SIZE strSize;
	
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
			hInst = (HINSTANCE)GetModuleHandle("cmifex.pyd");
			hNCursor = LoadCursor(hInst, MAKEINTRESOURCE(IDC_POINT_HAND2));			
			break;

		case G_HAND:
			hInst = (HINSTANCE)GetModuleHandle("cmifex.pyd");
			hNCursor = LoadCursor(hInst, MAKEINTRESOURCE(IDC_GRAB_HAND2));			
			break;

		case U_STRECH:
			hInst = (HINSTANCE)GetModuleHandle("cmifex.pyd");
			hNCursor = LoadCursor(hInst, MAKEINTRESOURCE(IDC_U_STRECH));			
			break;

		case D_STRECH:
			hInst = (HINSTANCE)GetModuleHandle("cmifex.pyd");
			hNCursor = LoadCursor(hInst, MAKEINTRESOURCE(IDC_D_STRECH));			
			break;

		case L_STRECH:
			hInst = (HINSTANCE)GetModuleHandle("cmifex.pyd");
			hNCursor = LoadCursor(hInst, MAKEINTRESOURCE(IDC_L_STRECH));			
			break;

		case R_STRECH:
			hInst = (HINSTANCE)GetModuleHandle("cmifex.pyd");
			hNCursor = LoadCursor(hInst, MAKEINTRESOURCE(IDC_R_STRECH));			
			break;

		case UL_STRECH:
			hInst = (HINSTANCE)GetModuleHandle("cmifex.pyd");
			hNCursor = LoadCursor(hInst, MAKEINTRESOURCE(IDC_UL_STRECH));			
			break;

		case UR_STRECH:
			hInst = (HINSTANCE)GetModuleHandle("cmifex.pyd");
			hNCursor = LoadCursor(hInst, MAKEINTRESOURCE(IDC_UR_STRECH));			
			break;

		case DR_STRECH:
			hInst = (HINSTANCE)GetModuleHandle("cmifex.pyd");
			hNCursor = LoadCursor(hInst, MAKEINTRESOURCE(IDC_RD_STRECH));			
			break;

		case DL_STRECH:
			hInst = (HINSTANCE)GetModuleHandle("cmifex.pyd");
			hNCursor = LoadCursor(hInst, MAKEINTRESOURCE(IDC_LD_STRECH));			
			break;

		case PUT:
			hInst = (HINSTANCE)GetModuleHandle("cmifex.pyd");
			hNCursor = LoadCursor(hInst, MAKEINTRESOURCE(IDC_PUT));			
			break;

		case WAIT:
			 //hNCursor = LoadCursor(NULL, IDC_WAIT);
			hInst = (HINSTANCE)GetModuleHandle("cmifex.pyd");
			hNCursor = LoadCursor(hInst, MAKEINTRESOURCE(IDC_WATCH2));
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
	RECT box;
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

static PyObject* py_cmifex_Broadcast(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	int id;

	if(!PyArg_ParseTuple(args, "i", &id))
	{
		CmifExErrorFunc("BroadcastMessage(id)");
		Py_INCREF(Py_None);
		return Py_None;
	}
	
	PostMessage(HWND_BROADCAST, id, 0, 0);	
		
	return Py_BuildValue("i", 1);
} 



static PyObject* py_cmifex_SetSiblings(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	int flag=1;
	LONG style=0;
	//char str[30];
	
	if(!PyArg_ParseTuple(args, "Oi", &ob, &flag))
	{
		CmifExErrorFunc("SetSiblings(Window, flag)");
		Py_INCREF(Py_None);
		return Py_None;
	}
	hCWnd = GetWndPtr( ob );

	style = GetWindowLong(hCWnd->m_hWnd, GWL_EXSTYLE);
	//sprintf(str, "Flags: %.0f", (float)style);
	//hCWnd->MessageBox(str, "style", MB_OK);
	if (flag==1)
		style = style|WS_EX_TRANSPARENT;
	else if (flag==0)
		style = style&~WS_EX_TRANSPARENT;

	SetWindowLong(hCWnd->m_hWnd, GWL_EXSTYLE, style);
	
	//sprintf(str, "Flags: %.0f", (float)style);
	//hCWnd->MessageBox(str, "style", MB_OK);
	Py_INCREF(Py_None);
	return Py_None;
} //static PyObject* py_cmifex_SetSiblings(PyObject *self, PyObject *args)




static PyObject* py_cmifex_SetScrollInfo(PyObject *self, PyObject *args)
{
	CWnd *obWnd;
	PyObject *testOb = Py_None;//, *tmp;
	int sb, min, max, page, pos, visible;
		
	if(!PyArg_ParseTuple(args, "Oiiiiii", &testOb, &sb, &min, &max, &page, &pos, &visible))
	{
		CmifExErrorFunc("SetScrollInfo(Window, scrollbar, min, max, page, pos, visible)");
		Py_INCREF(Py_None);
		return Py_None;
	}

	obWnd =(CWnd*) GetWndPtr(testOb);
	
	SCROLLINFO si;
	si.fMask = SIF_PAGE | SIF_RANGE | SIF_POS;
	si.nMin = min;
	si.nMax = max;
	si.nPos = pos;
	si.nPage = page;

	if (visible == 1)
		obWnd->SetScrollInfo (sb, &si, TRUE);
	else
		obWnd->SetScrollInfo (sb, &si, FALSE);
	
	Py_INCREF(Py_None);
	return Py_None;
}


static PyObject* py_cmifex_LockWindowUpdate(PyObject *self, PyObject *args)
{	
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	
	if(!PyArg_ParseTuple(args, "O", &ob))
	{
		CmifExErrorFunc("LockWindowUpdate(Window)");
		Py_INCREF(Py_None);
		return Py_None;
	}	

	hCWnd = GetWndPtr( ob );	
	hCWnd->LockWindowUpdate();
	
	Py_INCREF(Py_None);
	return Py_None;
} //static PyObject* py_cmifex_LockWindowUpdate(PyObject *self, PyObject *args)



static PyObject* py_cmifex_UnLockWindowUpdate(PyObject *self, PyObject *args)
{	
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	
	if(!PyArg_ParseTuple(args, "O", &ob))
	{
		CmifExErrorFunc("LockWindowUpdate(Window)");
		Py_INCREF(Py_None);
		return Py_None;
	}	

	hCWnd = GetWndPtr( ob );	
	hCWnd->UnlockWindowUpdate();
	
	Py_INCREF(Py_None);
	return Py_None;
} //static PyObject* py_cmifex_UnLockWindowUpdate(PyObject *self, PyObject *args)




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
	{ "DrawLines", py_cmifex_DrawLines, 1 },
	{ "DrawRectangle", py_cmifex_DrawRectangle, 1 },
	{ "FillPolygon", py_cmifex_FillPolygon, 1 },
	{ "FillRectangle", py_cmifex_FillRectangle, 1 },
	{ "ValidateRect", py_cmifex_ValidateRect, 1 },
	{ "SetBGColor", py_cmifex_SetBGColor, 1 },
	{ "BeginPaint", py_cmifex_BeginPaint, 1 },
	{ "EndPaint", py_cmifex_EndPaint, 1 },
	{ "UnLockWindowUpdate", py_cmifex_UnLockWindowUpdate, 1 },
	{ "LockWindowUpdate", py_cmifex_LockWindowUpdate, 1 },
	{ "SetSiblings", py_cmifex_SetSiblings, 1 },
	
	//Get... Funtions
	{ "GetTextMetrics", py_cmifex_GetTextMetrics, 1 },
	{ "GetScreenWidth", py_cmifex_GetScreenWidth, 1 },
	{ "GetScreenHeight", py_cmifex_GetScreenHeight, 1 },
	{ "GetScreenXDPI", py_cmifex_GetScreenXDPI, 1 },
	{ "GetScreenYDPI", py_cmifex_GetScreenYDPI, 1 },

	//Set... Functions
	{ "SetCursor", py_cmifex_SetCursor, 1 },
	{ "SetFlag", (PyCFunction)py_example_SetFlag, 1},
	{ "SetScrollInfo", (PyCFunction)py_cmifex_SetScrollInfo, 1},

	//Utilities 
	{ "ScreenToBox", py_cmifex_ScreenToBox, 1 },
	{ "ScreenToClient", py_cmifex_ScreenToClient, 1 },
	{ "BroadcastMessage", py_cmifex_Broadcast, 1},


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
