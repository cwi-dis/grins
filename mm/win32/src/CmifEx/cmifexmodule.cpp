#include "Python.h"
#include "stdafx.h"
#include "win32ui.h"
#include "win32assoc.h"
#include "win32cmd.h"
#include "win32win.h"

#include <string.h>
#include <math.h>
#include "winclass.h"

#include <GRiNSRes.h> // Resources defines in the GRiNS resource DLL.

#include "cmifexhelp.h"

myWin *GetMyWndPtr(PyObject *ob)
{
	CWnd *pWnd = GetWndPtr(ob);
	ASSERT(pWnd && pWnd->IsKindOf(RUNTIME_CLASS(myWin)));
	return (myWin *)pWnd;
}


#define LSIZE	10

static PyObject *CmifExError;
char cmifClass[100]="";
char dbgmess[100]="";
static PyObject *CallbackMap = NULL;

WNDPROC		orgProc;
BOOL flg=FALSE;

void GetAnchorList(myWin* hwnd, CString str, char* facename,
				   int sz,int id,CString align);
CString getanchor(CString& str, CString& tmp);

BOOL CheckIfIsSingleAnchor(CString str);
BOOL IsBlank(CString wrd);
void findxy(HWND hwnd,int& county,CString& str,CString name,
			int x,char* facename,int sz,int id,RECT rect2);
CString clearstring(CString str);

void puttext(HWND hwnd, char* str,char* facename,int size,int trasp,COLORREF bkcolor,COLORREF fontcolor,CString align);

CString findmaxword(HDC dc,CString word);
int countlines (HDC dc,CString str,char* fcname,int sz,RECT rect);
void findrect(HDC dc,CString str,char* fcname,int sz,CString bigline,CString algn,RECT r,RECT &r2);

BOOL IsAnchor(CString str);
void SaveList(int ID,CString anchor,int x1,int y1,int x2,int y2);

typedef enum { ARROW, WAIT, HAND, START, G_HAND, U_STRECH,
			   D_STRECH, L_STRECH, R_STRECH, UL_STRECH, 
			   UR_STRECH, DR_STRECH, DL_STRECH, PUT} Cursors;

HDC hdc=NULL;
PAINTSTRUCT ps;
static int nPaint=0;

#define EZ_ATTR_BOLD          1
#define EZ_ATTR_ITALIC        2
#define EZ_ATTR_UNDERLINE     4
#define EZ_ATTR_STRIKEOUT     8

static HFONT EzCreateFont (HDC hdc, char * szFaceName, int iDeciPtHeight,
                    int iDeciPtWidth, int iAttributes, BOOL fLogRes)
{
	FLOAT      cxDpi, cyDpi ;
	HFONT      hFont ;
	LOGFONT    lf ;
	POINT      pt ;
	TEXTMETRIC tm ;

	SaveDC (hdc) ;

	SetGraphicsMode (hdc, GM_ADVANCED) ;
	ModifyWorldTransform (hdc, NULL, MWT_IDENTITY) ;
	SetViewportOrgEx (hdc, 0, 0, NULL) ;
	SetWindowOrgEx   (hdc, 0, 0, NULL) ;

	if (fLogRes)
	{
		cxDpi = (FLOAT) GetDeviceCaps (hdc, LOGPIXELSX) ;
		cyDpi = (FLOAT) GetDeviceCaps (hdc, LOGPIXELSY) ;
	}
	else
	{
		cxDpi = (FLOAT) (25.4 * GetDeviceCaps (hdc, HORZRES) /
							GetDeviceCaps (hdc, HORZSIZE)) ;

		cyDpi = (FLOAT) (25.4 * GetDeviceCaps (hdc, VERTRES) /
							GetDeviceCaps (hdc, VERTSIZE)) ;
	}

	pt.x = (int) (iDeciPtWidth  * cxDpi / 72) ;
	pt.y = (int) (iDeciPtHeight * cyDpi / 72) ;

	DPtoLP (hdc, &pt, 1) ;

	lf.lfHeight         = - (int) (fabs (pt.y) / 10.0 + 0.5) ;
	lf.lfWidth          = 0 ;
	lf.lfEscapement     = 0 ;
	lf.lfOrientation    = 0 ;
	lf.lfWeight         = iAttributes & EZ_ATTR_BOLD      ? 700 : 0 ;
	lf.lfItalic         = iAttributes & EZ_ATTR_ITALIC    ?   1 : 0 ;
	lf.lfUnderline      = iAttributes & EZ_ATTR_UNDERLINE ?   1 : 0 ;
	lf.lfStrikeOut      = iAttributes & EZ_ATTR_STRIKEOUT ?   1 : 0 ;
	lf.lfCharSet        = 0 ;
	lf.lfOutPrecision   = 0 ;
	lf.lfClipPrecision  = 0 ;
	lf.lfQuality        = 0 ;
	lf.lfPitchAndFamily = 0 ;

	strcpy (lf.lfFaceName, szFaceName) ;

	hFont = CreateFontIndirect (&lf) ;

	if (iDeciPtWidth != 0)
	{
		hFont = (HFONT) SelectObject (hdc, hFont) ;

		GetTextMetrics (hdc, &tm) ;

		DeleteObject (SelectObject (hdc, hFont)) ;

		lf.lfWidth = (int) (tm.tmAveCharWidth *
								fabs (pt.x) / fabs (pt.y) + 0.5) ;

		hFont = CreateFontIndirect (&lf) ;
	}

	RestoreDC (hdc, -1) ;

	return hFont ;
}



static LRESULT CALLBACK MyWndProc (HWND hwnd, UINT iMsg, WPARAM wParam, LPARAM lParam)
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

static PyObject *CmifExErrorFunc(char *str)
{
	PyErr_SetString (CmifExError, str);
	return NULL;
}


static PyObject* py_cmifex_CreateWindow(PyObject *self, PyObject *args)
{
	char *wndName;
	PyObject *testOb = Py_None;
	CWnd *newWnd, *mainWnd;
	PyCWnd *testWnd;
	int x=100, y=100, nWidth=200, nHeight=200, visible;
	DWORD ws_flags;
	
	newWnd = new myWin;

	if(!PyArg_ParseTuple(args, "siiiii", &wndName, &x, &y, &nWidth, &nHeight, &visible))
		return NULL;

	TRACE("%s, X: %d, Y: %d, W: %d, H: %d\n", wndName, x, y, nWidth, nHeight );
	
	mainWnd = AfxGetMainWnd();
	
	if(visible)
		ws_flags = WS_OVERLAPPEDWINDOW | WS_VISIBLE | WS_CLIPCHILDREN | WS_HSCROLL | WS_VSCROLL;  
	else
		ws_flags = WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN | WS_HSCROLL | WS_VSCROLL;  
	
	if(cmifClass[0]==0)
		strcpy(cmifClass, AfxRegisterWndClass(CS_DBLCLKS, AfxGetApp()->LoadCursor (IDC_ARROW), (HBRUSH) GetStockObject (WHITE_BRUSH), AfxGetApp()->LoadIcon(MAKEINTRESOURCE(IDR_PYTHON))));

	if(newWnd->CreateEx(WS_EX_CLIENTEDGE,
						cmifClass, wndName,
						ws_flags,
						x, y, nWidth, nHeight,
						NULL,
						/*mainWnd->m_hWnd,*/
						NULL))
		TRACE("CmifEx CreateWindow OK!\n");
	else
		RETURN_ERR("CmifEx CreateWindow FALSE!\n");
	
	orgProc = (WNDPROC)SetWindowLong(newWnd->m_hWnd, GWL_WNDPROC, (LONG)MyWndProc);

	testWnd = testWnd->make(testWnd->type, newWnd);
	testOb = testWnd->GetGoodRet();

	return Py_BuildValue("O", testOb);
} //static PyObject* py_cmifex_CreateWindow(PyObject *self, PyObject *args)



static PyObject* py_example_SetFlag(PyObject *self, PyObject *args)
{
	int x;
			
	if(!PyArg_ParseTuple(args, "i", &x))
		return NULL;

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
		return NULL;

	newWnd = new myWin;
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
  
	testWnd = testWnd->make(testWnd->type, newWnd);
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
		return NULL;

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
		return NULL;

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
		return NULL;

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
		return NULL;

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
		return NULL;

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
		return NULL;

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
		return NULL;


	hCWnd = GetWndPtr( ob );	
	if((hdc = GetDC(hCWnd->m_hWnd))==NULL)
		MessageBox(hCWnd->m_hWnd, "NULL HDC!", "Debug", MB_ICONSTOP|MB_OK);	

	if((hPen = (HPEN)SelectObject(hdc, CreatePen(PS_SOLID, 0, RGB(r, g, b))))==NULL)
		return CmifExErrorFunc("DrawLine: NULL PEN!");

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
		return NULL;

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
	char *string;
	int top, left;
	static int times=1;

	if(!PyArg_ParseTuple(args, "O(iis)",
							&ob, &left, &top, &string))
		return NULL;

	hCWnd = GetWndPtr( ob );	
	if((hdc = GetDC(hCWnd->m_hWnd))==NULL)
		MessageBox(hCWnd->m_hWnd, "NULL HDC!", "Debug", MB_ICONSTOP|MB_OK);	
	
	TextOut(hdc, left, top, string, strlen(string));

	ReleaseDC(hCWnd->m_hWnd, hdc);
	
	RETURN_NONE;
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
	HBRUSH hBrush ;
	HPEN hPen;
	int r, g, b, npts_list, polyMode, i;
	static int times=1;

	if (!PyArg_ParseTuple(args, "OO(iii)", &ob, &list,  &r, &g, &b))
		return NULL;

	if (!checkshortlist(2, list, (long**)&pts_list, &npts_list))
		if (!PyErr_Occurred())
			PyErr_SetString(PyExc_TypeError, "list should be Point[]");

	if((pts = (POINT*)malloc(npts_list*sizeof(POINT)))==NULL)
		return CmifExErrorFunc("FillPolygon: Not Enough Memory!");

	for(i=0; i<npts_list; i++)
	{
		pts[i].x = pts_list[i*2];
		pts[i].y = pts_list[i*2+1];
	}

	hCWnd = GetWndPtr( ob );	
	if((hdc = GetDC(hCWnd->m_hWnd))==NULL)
		return CmifExErrorFunc("FillPolygon: NULL HDC!");
	
	if((hBrush = (HBRUSH)SelectObject(hdc, CreateSolidBrush (RGB(r, g, b))))==NULL)
		return CmifExErrorFunc("FillPolygon: NULL BRUSH!");

	if((hPen = (HPEN)SelectObject(hdc, CreatePen(PS_SOLID, 0, RGB(r, g, b))))==NULL)
		return CmifExErrorFunc("FillPolygon: NULL PEN!");

	polyMode = SetPolyFillMode(hdc, WINDING);
	Polygon(hdc, pts, npts_list);
	polyMode = SetPolyFillMode(hdc, polyMode);

	free(pts);

	DeleteObject ((HBRUSH)SelectObject(hdc, hBrush)) ;
	DeleteObject ((HPEN)SelectObject(hdc, hPen)) ;
	ReleaseDC(hCWnd->m_hWnd, hdc);
	
	RETURN_NONE;
} //static PyObject* py_cmifex_FillPolygon(PyObject *self, PyObject *args)


static PyObject* py_cmifex_DrawLines(PyObject *self, PyObject *args)
{
	PyObject *list=Py_None, *ob=Py_None;
	long *pts_list; 
	POINT *pts;
	CWnd *hCWnd;
	HDC hdc=NULL;
	HPEN hPen;
	int r, g, b, npts_list, i;
	static int times=1;

	if (!PyArg_ParseTuple(args, "OO(iii)", &ob, &list,  &r, &g, &b))
		return NULL;

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
	
	RETURN_NONE;
} //static PyObject* py_cmifex_DrawLines(PyObject *self, PyObject *args)


static PyObject* py_cmifex_FillRectangle(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	HDC hdc=NULL;
	HBRUSH hBrush ;
    RECT   rect ;
	int top, left, right, bottom;
	int r, g, b;
	static int times=1;

	if(!PyArg_ParseTuple(args, "O(iiii)(iii)",
							&ob, &left, &top, &right, &bottom, &r, &g, &b))
		return NULL;

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

	RETURN_NONE;
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
		return NULL;
		
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
		return NULL;

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
		return NULL;

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
		return NULL;

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
		return NULL;

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
		return NULL;

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
		return NULL;

	hWnd = GetActiveWindow();
	hdc = GetDC(hWnd);
	nDPI = GetDeviceCaps(hdc, LOGPIXELSY);
	ReleaseDC(hWnd, hdc);

	return Py_BuildValue("i", nDPI);
} //static PyObject* py_cmifex_GetScreenYDPI(PyObject *self, PyObject *args)

static PyObject* py_cmifex_SetCursor(PyObject *self, PyObject *args)
{
	HCURSOR hPCursor, hNCursor;
	Cursors nCursor;
	int ret=0;

	if(!PyArg_ParseTuple(args, "i", &nCursor))
		return NULL;

	switch(nCursor)
	{
		case ARROW:
			hNCursor = LoadCursor(NULL, IDC_ARROW);			
			break;				

		case HAND:
			hNCursor = AfxGetApp()->LoadCursor(MAKEINTRESOURCE(IDC_POINT_HAND2));			
			break;

		case G_HAND:
			hNCursor = AfxGetApp()->LoadCursor(MAKEINTRESOURCE(IDC_GRAB_HAND2));			
			break;

		case U_STRECH:
			hNCursor = AfxGetApp()->LoadCursor(MAKEINTRESOURCE(IDC_U_STRECH));			
			break;

		case D_STRECH:
			hNCursor = AfxGetApp()->LoadCursor(MAKEINTRESOURCE(IDC_D_STRECH));			
			break;

		case L_STRECH:
			hNCursor = AfxGetApp()->LoadCursor(MAKEINTRESOURCE(IDC_L_STRECH));			
			break;

		case R_STRECH:
			hNCursor = AfxGetApp()->LoadCursor(MAKEINTRESOURCE(IDC_R_STRECH));			
			break;

		case UL_STRECH:
			hNCursor = AfxGetApp()->LoadCursor(MAKEINTRESOURCE(IDC_UL_STRECH));			
			break;

		case UR_STRECH:
			hNCursor = AfxGetApp()->LoadCursor(MAKEINTRESOURCE(IDC_UR_STRECH));			
			break;

		case DR_STRECH:
			hNCursor = AfxGetApp()->LoadCursor(MAKEINTRESOURCE(IDC_RD_STRECH));			
			break;

		case DL_STRECH:
			hNCursor = AfxGetApp()->LoadCursor(MAKEINTRESOURCE(IDC_LD_STRECH));			
			break;

		case PUT:
			hNCursor = AfxGetApp()->LoadCursor(MAKEINTRESOURCE(IDC_PUT));			
			break;

		case WAIT:
			 //hNCursor = LoadCursor(NULL, IDC_WAIT);
			hNCursor = AfxGetApp()->LoadCursor(MAKEINTRESOURCE(IDC_WATCH2));
			break;
			
		case START:
			hNCursor = LoadCursor(NULL, IDC_APPSTARTING);			
	}
	ASSERT(hNCursor); // Resource not in a loaded DLL!
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
		return NULL;
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
		return NULL;
	hCWnd = GetWndPtr( ob );
	hCWnd->ScreenToClient(&pt);
	return Py_BuildValue("ii", pt.x, pt.y);
} //static PyObject* py_cmifex_ScreenToClient(PyObject *self, PyObject *args)

static PyObject* py_cmifex_Broadcast(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	int id;

	if(!PyArg_ParseTuple(args, "i", &id))
		return NULL;
	
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
		return NULL;
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
		return NULL;

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
		return NULL;

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
		return NULL;

	hCWnd = GetWndPtr( ob );	
	hCWnd->UnlockWindowUpdate();
	
	Py_INCREF(Py_None);
	return Py_None;
} //static PyObject* py_cmifex_UnLockWindowUpdate(PyObject *self, PyObject *args)

/////////////////////////////////////////////////////////////////////////////////
//
// TEXT RELATED FUNCTIONS.  MERGED FROM TEXTEXMODULE.CPP
//

/*
FUNCTION : findmaxword
ATTRIBUTES :
	HDC dc: The context of the window
	CString word: The text of the window
NOTES:
	This function finds the bigest line in the text, that ends with 
a '\n' and returns it. The function calculates the length of the 
function in pixel units and not in characters.
*/


CString findmaxword(HDC dc,CString word)
{
	int x,maxw=0;
	CString tmp=word,tmp2="";
	SIZE size;
	
	x=tmp.Find('\n');
	while(x!=-1)
	{
		SetTextJustification(dc,0,0);
		GetTextExtentPoint32(dc,(LPCTSTR)tmp,x,&size);
		if(size.cx>maxw)
		{
			maxw=size.cx;
			tmp2=tmp.Mid(0,x);
		}
		tmp=tmp.Mid(x+1);
		x=tmp.Find('\n');
	}

	SetTextJustification(dc,0,0);
	GetTextExtentPoint32(dc,(LPCTSTR)tmp,tmp.GetLength(),&size);
	if(size.cx>maxw) tmp2=tmp;
	//if(tmp2.IsEmpty()) tmp2=tmp;
	
	return tmp2;
}



/*
FUNCTION : expandtabs
ATTRIBUTES :
	CString str: The text that is associated with the window.
	CString align: A string that contains flags for the style 
				   of the text. It is empty if the text belongs 
				   to a text channel.
NOTES:
	This function expands the tabs and replaces the first '\n'
character of every sequence of '\n''s in the text, with a space.
It returns the new text.
*/


CString expandtabs(CString str,CString align)
{
	CString tmp,tmp2="";
	int x,y;
	 
	tmp=str;
	//tmp2 will hold the new text.
	//While there is a tab in the text
	//replace it whith four spaces
	while(tmp.Find('\t')!=-1)
	{
		x = tmp.Find('\t');
		tmp2 += tmp.Left(x)+"    ";
		tmp = tmp.Mid(x+1);
	}
	
	tmp2+=tmp;

	//Only if the text belongs to a text channel and not 
	//for the label channel
	if(align.IsEmpty())
	{
		tmp = tmp2;
		tmp2.Empty();
		
		//While there is a '\n' in the text
		while(tmp.Find('\n')!=-1)
		{
			//Find the first '\n' and replace it with a space
			x = tmp.Find('\n');
			tmp.SetAt(x,' ');
			tmp2 += tmp.Left(x+1);
			y = tmp.Find('\n');
			//Find the end of the sequence of '\n's
			while(x+1==y)
			{
				x = y;
				tmp2 += tmp[x];
				tmp.SetAt(x,' ');
				y = tmp.Find('\n');
			}
			
			//Take the rest of the text
			tmp = tmp.Mid(x+1);
		}

		tmp2+=tmp;
	}
		
	return tmp2;
}



/*
FUNCTION : countlines
ATTRIBUTES :
	HDC dc: The context of the window
	CString str: The text of the window
	char* fcname: The face name of the font in use.
	int sz: Size of the font.
	RECT rect: The rectangle where the text will be placed.
NOTES:
	This function finds the height of the text in pixel units and 
returns it. 
*/



int countlines (HDC dc,CString str,char* fcname,int sz,RECT rect)
{
	//ASSERT(0);
	//HDC dc = ::GetDC(this->m_hWnd);
	int county=0;
	SIZE size;
	int counter,oldcounter;
	CString tmp = str,tmpwrd;
	HFONT hfont;
	TEXTMETRIC tm;

	if(fcname)
	{
		hfont=EzCreateFont(dc, fcname, sz*10, 0, 0, TRUE);
		::SelectObject(dc,hfont);

		GetTextMetrics(dc,&tm);
	
		counter=oldcounter=0;

		while(counter<tmp.GetLength())
		{
			if((tmp[counter]==' ')||(tmp[counter]==0))
			{
				SetTextJustification(dc,0,0);
				GetTextExtentPoint32(dc,(LPCTSTR)tmp,counter,&size);
			
				if(size.cx>rect.right)
				{
					if(!tmp.IsEmpty())
						{
							if((tmp[0]==' ')&&(oldcounter==0)) county+=1;
						}
					
					if(oldcounter==0) tmp=tmp.Mid(counter+1);
					else tmp=tmp.Mid(oldcounter+1);

					if(oldcounter==0) counter=-1; 
					else counter=counter-oldcounter-1;

					oldcounter=0;
					county+=1;
				}

				if(counter!=-1) oldcounter=counter;
				counter++;
				continue;
			}

			if(tmp[counter]=='\n')
			{
				if(counter==0) GetTextExtentPoint32(dc,(LPCTSTR)tmp,counter,&size); 
				else GetTextExtentPoint32(dc,(LPCTSTR)tmp,counter,&size);
			
				if(size.cx>rect.right)
				{
					county+=1;
					if(oldcounter==0)tmpwrd = tmp.Mid(oldcounter,counter-oldcounter);
					else tmpwrd = tmp.Mid(oldcounter+1,counter-oldcounter);
					SetTextJustification(dc,0,0);
					GetTextExtentPoint32(dc,(LPCTSTR)tmpwrd,tmpwrd.GetLength(),&size);
					if(size.cx>rect.right) county+=1;
				}
			
				tmp=tmp.Mid(counter+1);

				counter=-1;
				oldcounter=0;
				county+=1;

			}

			counter++;
		}

		if(!tmp.IsEmpty()) 
		{
			::SetTextJustification(dc,0,0);
			::GetTextExtentPoint32(dc,(LPCTSTR)tmp,tmp.GetLength(),&size);
			if(size.cx>rect.right) county+=1;
			county+=1;
		}
		
		::DeleteObject(SelectObject(dc, GetStockObject(SYSTEM_FONT)));
	
		//::ReleaseDC(this->m_hWnd,dc);
	}
	
	return (county*tm.tmHeight);
}




/*
FUNCTION : findrect
ATTRIBUTES :
	HDC dc: The context of the window
	CString str: The text of the window
	char* fcname: The face name of the font in use.
	int sz: Size of the font.
	CString bigline: The bigest line in the text.
	CString algn: A string that contains flags for the style 
				  of the text. It is empty if the text belongs 
				  to a text channel.
	RECT r: The client area of the window.
NOTES:
	This function finds the rectangle where the text of the window
will be placed and returns. If we have a text channel the rectangle is the whole 
client area, else if we have a label channel the rectangle depends of the algn parameter. 
*/



void findrect(HDC dc,CString str,char* fcname,int sz,CString bigline,CString algn,RECT r,RECT &r2)
{
	SIZE size;
	HFONT hfont=NULL;
	RECT tmprect,rectangle;

	tmprect.top=tmprect.left=0;
	tmprect.bottom = r.bottom;
		
	if(fcname!=NULL) hfont = EzCreateFont(dc, fcname, sz*10, 0, 0, TRUE);
	::SelectObject(dc, hfont);
	
	::SetTextJustification(dc,0,0);
	::GetTextExtentPoint32(dc,(LPCTSTR)bigline,bigline.GetLength(),&size);
		
	::DeleteObject(SelectObject(dc, GetStockObject(SYSTEM_FONT)));
	
	tmprect.right = size.cx;

	if((algn.Find("center")==-1)&&(algn.Find("top")==-1)&&
		(algn.Find("bottom")==-1)&&(algn.Find("right")==-1)&&(algn.Find("left")==-1))
	{
		rectangle = r; 
	}
	else
	{
		if(algn.Find("center")>-1) 
		{
			rectangle.left = (r.right-size.cx)/2;
			rectangle.right = rectangle.left+size.cx;
			rectangle.top = (r.bottom-countlines(dc,str,fcname,sz,tmprect))/2;
			rectangle.bottom = rectangle.top+countlines(dc,str,fcname,sz,tmprect);
		}
		else
		{
			if((algn.Find("top")>-1)&&(algn.Find("bottom")>-1))
			{
				rectangle.top = (r.bottom-countlines(dc,str,fcname,sz,tmprect))/2;
				rectangle.bottom = rectangle.top+countlines(dc,str,fcname,sz,tmprect);
			}
			else
			{
				if(algn.Find("top")>-1) 
				{
					rectangle.top = 0;
					rectangle.bottom = countlines(dc,str,fcname,sz,tmprect);
				}
				else if(algn.Find("bottom")>-1) 
				{
					rectangle.top = r.bottom-countlines(dc,str,fcname,sz,tmprect);
					rectangle.bottom = r.bottom;
				}
				else
				{
					rectangle.top = (r.bottom-countlines(dc,str,fcname,sz,tmprect))/2;
					rectangle.bottom = rectangle.top+countlines(dc,str,fcname,sz,tmprect);
				}
			}
			
			
			if((algn.Find("right")>-1)&&(algn.Find("left")>-1))
			{
				rectangle.left = (r.right-size.cx)/2;
				rectangle.right = rectangle.left+size.cx;
			}
			else
			{
				if(algn.Find("right")>-1) 
				{
					rectangle.left = r.right-size.cx;
					rectangle.right = r.right;
				}
				else if(algn.Find("left")>-1) 
				{
					rectangle.left = 0;
					rectangle.right = size.cx;
				}
				else
				{
					rectangle.left = (r.right-size.cx)/2;
					rectangle.right = rectangle.left+size.cx;
				}
			}
		}
	}
	
	r2 = rectangle;
}




/*
FUNCTION : CheckIfIsSingleAnchor
ATTRIBUTES :
	CString str: The text of the window
NOTES:
	This function returns true if the document is an anchor. 
*/


BOOL CheckIfIsSingleAnchor(CString str)
{
	CString tmp = str;
	int x,y;
	BOOL total;

	tmp.MakeLower();
	x = tmp.Find("<a");
	if(x==-1) return FALSE;
	if((x>tmp.Find("name="))||(tmp.Find("name=")==-1)) return FALSE;
	y = tmp.Find("</a>");
	if(y==-1) y = tmp.Find("<\\a>");
	if((y==-1)||(y<tmp.Find("name="))) return FALSE;
	if((x<=2)&&(y+4+3>=tmp.GetLength())) total = TRUE;
	else total = FALSE;

	return total;
}




/*
FUNCTION : IsBlank
ATTRIBUTES :
	CString wrd: A string
NOTES:
	This function returns true if wrd contains only spaces
and '\n'.
*/


BOOL IsBlank(CString wrd)
{
	int x,y;
	BOOL flag=TRUE;
	
	y = wrd.GetLength();
	for(x=0;x<y;x++)
		if((wrd[x]!=' ')&&(wrd[x]!='\n')) 
		{
			flag = FALSE;
			break;
		}

	return flag;
}




/*
FUNCTION : GetAnchorList
ATTRIBUTES :
	CWnd hwnd: The handler of the window
	CString str: The text of the window
	char* facename: The face name of the font in use.
	int sz: Size of the font.
	int id: An index to a function
	CString align: A string that contains flags for the style 
				   of the text. It is empty if the text belongs 
				   to a text channel.
NOTES:
	This function finds the anchors in the text and calls the findxy
function to calculate their coordinates.
*/

void GetAnchorList(myWin* hwnd, CString str, char* facename,int sz,int id,CString align)
{
	CString s1,tmp,name,bline;
	int x,county=0,charid;
	RECT rect,tmprect,windowrect;
	
	::GetClientRect(hwnd->m_hWnd,&rect);
	::GetWindowRect(hwnd->m_hWnd,&windowrect);

	HDC dc = ::GetDC(hwnd->m_hWnd);
	bline = findmaxword(dc,clearstring(str));
	findrect(dc,clearstring(str),facename,sz,bline,align,rect,tmprect);
	
	if(align.IsEmpty())
	{
		//if is a text channel
		//HBRUSH hbr;
		if(tmprect.bottom < countlines(dc,clearstring(str),facename,sz,tmprect))
		{
			if(rect.right>windowrect.right-windowrect.left-(::GetSystemMetrics(SM_CXVSCROLL)))
			{
				tmprect.right -= ::GetSystemMetrics(SM_CXVSCROLL);
			}
		}
		//hbr = CreateSolidBrush(RGB(0, 0, 255));
		//FrameRect(dc, &tmprect, hbr);
		//DeleteObject(hbr);
	}
	
	::ReleaseDC(hwnd->m_hWnd,dc);
	
	s1=str;
	
	if((CheckIfIsSingleAnchor(s1))&&(IsAnchor(s1)))
	{
		name=getanchor(s1, tmp);
		if(align.IsEmpty())
		{
			//if is a text channel
		//	if(tmprect.bottom < countlines(dc,clearstring(str),facename,sz,tmprect))
		//	tmprect.bottom = countlines(dc,clearstring(str),facename,sz,tmprect);
			tmprect.top = rect.top;
			tmprect.bottom = rect.bottom;
		}
		else
		{
			tmprect = rect;
		}
		hwnd->single_anchor = TRUE;
		if (id!=-1) SaveList(id,name,
				    tmprect.left,tmprect.top,
				    tmprect.right,tmprect.bottom);
						
	}
	else
	{
		while(s1.GetLength()!=0)
		{
			x=s1.Find('<');
			if(x!=-1)
			{
				if(IsAnchor(s1))
				{
					tmp+=s1.Left(x);
					charid = tmp.GetLength();
					s1=s1.Mid(x);
					name=getanchor(s1, tmp);
					findxy(hwnd->m_hWnd,county,tmp,name,charid,facename,sz,id,tmprect);	
				}
				else
				{
					tmp+=s1.Left(x+1);
					s1=s1.Mid(x+1);
				}
				
			}
			else s1.Empty();
		}
	}
}



/*
FUNCTION : IsAnchor
ATTRIBUTES :
	CString str: A string
NOTES:
	This function finds if there is a "good" anchor in the str.
*/

BOOL IsAnchor(CString str)
{
	int x=0,y=0;
	CString tmp;
	
	if(str.IsEmpty())
		return FALSE;

	tmp=str;
	x=tmp.Find('<');

	y=tmp.Find('=');
	if((y==-1)||(y<x)) return FALSE;

	tmp=tmp.Mid(x,y-x+1);
	x=0;
	 
	while(tmp[x]!='=')
	{
		if(tmp[x]==' ')
		{
			tmp=tmp.Mid(0,x)+tmp.Mid(x+1);
			continue;
		}
		x++;
	}
	
	
	tmp.MakeUpper();
	if(strcmp((LPCTSTR)tmp,"<ANAME=")==0)
	{
		if((str.Find("<\\A>")==-1)&&(str.Find("<\\a>")==-1)&&(str.Find("</a>")==-1)&&(str.Find("</A>")==-1)) return FALSE;
		else return TRUE;
	}
	else return FALSE;
}



/*
FUNCTION : getanchor 
ATTRIBUTES :
	CString str: A string that contains the unchecked text for 
				 anchors
	CString tmp: A string that contains the checked text for anchors
NOTES:
	This function returns the string index of the anchor.
*/

CString getanchor(CString &str, CString &tmp)
{

	CString name,fullanchor;
	int x,y;

	x=str.Find('<');
	str=str.Mid(x);
	x=str.Find('=');
	x++;
	str=str.Mid(x);
	
	while(str[0]==' ')
	{
		str=str.Mid(1);
		x++;
	}

	y=str.Find('>');
	name=str.Left(y);
	
	str=str.Mid(y+1);
    
	x=str.Find("</a>");
	if(x==-1) x=str.Find("</A>");
	if(x==-1) x=str.Find("<\\a>");
	if(x==-1) x=str.Find("<\\A>");
	fullanchor=str.Mid(0,x);

	y=name.GetLength();
	while(name[y-1]==' ') y--;
	name=name.Left(y);

	str=str.Mid(x+4);

	tmp+=fullanchor;
	
	return name;
}




/*
FUNCTION : findxy
ATTRIBUTES :
	HWND hwnd: The handler of the window
	int county: The number of the lines of the text
	CString str: A string that contains the checked text for 
				 anchors
	CString name: The string index of the anchor
	int x: The position of the first charachter of the anchor
	char* facename: The face name of the font in use.
	int sz: Size of the font
	int id: An index to a function 
	RECT rect2: The area where the text will be displayed
NOTES:
	This function finds the coordinates of the anchor in the str.
*/

void findxy(HWND hwnd,int& county,CString& str,CString name,
			int x,char* facename,int sz,int id,RECT rect2)			
{
	RECT rect;
	SIZE size;
	TEXTMETRIC tm;
	HDC dc;
	HFONT hfont;
	int counter,oldcounter,newcounter,charid;
	CString wrd,tmpwrd;

	size.cx = size.cy = 0;

	dc=GetDC(hwnd);

	rect=rect2;

	hfont = EzCreateFont(dc, facename, sz*10, 0, 0, TRUE);
	SelectObject(dc, hfont);

	GetTextMetrics(dc,&tm);

	tm.tmHeight+=tm.tmExternalLeading/2;
	
	counter=oldcounter=newcounter=charid=0;


	while(counter<str.GetLength())
	{
		if(charid==x) break;
		
		if((str[counter]==' ')||(str[counter]==0))
		{
			SetTextJustification(dc,0,0);
			GetTextExtentPoint32(dc,(LPCTSTR)str,counter,&size);
			
			if(size.cx>rect2.right-rect2.left)
			{
				if(oldcounter==0) str=str.Mid(counter+1);
				else str=str.Mid(oldcounter+1);

				if(oldcounter==0) counter=-1; 
				else counter=counter-oldcounter-1;
				
				oldcounter=0;
				county+=1;
			}

			if(counter!=-1) oldcounter=counter;
			counter++;
			charid++;
			continue;
		}

		if(str[counter]=='\n')
		{
			SetTextJustification(dc,0,0);
			if(counter==0) GetTextExtentPoint32(dc,(LPCTSTR)str,counter+1,&size); 
			else GetTextExtentPoint32(dc,(LPCTSTR)str,counter,&size);
			
			if(size.cx>rect2.right-rect2.left) county+=1;

			if(oldcounter==0)tmpwrd = str.Mid(oldcounter,counter-oldcounter-1);
			else tmpwrd = str.Mid(oldcounter+1,counter-oldcounter-1);
			SetTextJustification(dc,0,0);
			GetTextExtentPoint32(dc,(LPCTSTR)tmpwrd,tmpwrd.GetLength(),&size);
			if(size.cx>rect2.right-rect2.left) county+=1;
			str=str.Mid(counter+1);

			counter=-1;
			oldcounter=0;
			county+=1;

		}

		counter++;
		charid++;
	}
	
	
	newcounter=oldcounter=counter;
	wrd = str.Mid(counter);

	while(counter<str.GetLength())
	{
		if(str[counter]==' ')
		{
			SetTextJustification(dc,0,0);
			GetTextExtentPoint32(dc,(LPCTSTR)str,counter,&size);
			
			if(size.cx>rect2.right-rect2.left)
			{
				if(oldcounter!=newcounter) 
					wrd=str.Mid(oldcounter,newcounter-oldcounter+1);
		     	else if(newcounter==0) wrd=str.Mid(oldcounter,counter-oldcounter+1);
				else wrd=str.Mid(oldcounter,newcounter-oldcounter+1);

				SetTextJustification(dc,0,0);
				if(oldcounter!=0) GetTextExtentPoint32(dc,(LPCTSTR)str,oldcounter,&size);
				else size.cx=0;
	
				rect.left=rect2.left+size.cx;

				SetTextJustification(dc,0,0);
				GetTextExtentPoint32(dc,(LPCTSTR)wrd,wrd.GetLength(),&size);

				if(!wrd.IsEmpty())
				{
					if((wrd[0]==' ')&&(size.cx>rect2.right-rect2.left)&&(newcounter==0)) county+=1;
				}

				rect.right=rect.left+size.cx;
				
				rect.top=rect2.top+county*tm.tmHeight;
				rect.bottom=rect2.top+(county+1)*tm.tmHeight;
			
				
				if(!IsBlank(wrd))
				{
					if ((id!=-1)&&(rect.left!=rect.right)) 
								 SaveList(id,name,
								 rect.left,rect.top,
								 rect.right,rect.bottom); 
				}
				
				if(newcounter==0) str=str.Mid(counter+1);
				else str=str.Mid(newcounter+1);

				counter=-1; 
				oldcounter=0;
				newcounter = 0;
				county+=1;
				wrd = str.Mid(counter+1);
			}

			if(counter!=-1) newcounter=counter;
			counter++;
			continue;
		}

		if(str[counter]=='\n')
		{
			SetTextJustification(dc,0,0);
			if(counter==0) GetTextExtentPoint32(dc,(LPCTSTR)str,counter+1,&size); 
			else GetTextExtentPoint32(dc,(LPCTSTR)str,counter,&size);
			
			if(size.cx>rect2.right-rect2.left)
			{
				if(oldcounter!=newcounter) 
					wrd=str.Mid(oldcounter,newcounter-oldcounter+1);
		     	else if(newcounter==0) wrd=str.Mid(oldcounter,counter-oldcounter+1);
				else wrd=str.Mid(oldcounter,counter-oldcounter+1);

				if(wrd[0]==' ') 
				{
					oldcounter = 0;
					county+=1;
				}

								
				rect.top=rect2.top+county*tm.tmHeight;
				rect.bottom=rect2.top+(county+1)*tm.tmHeight;
			
				
				SetTextJustification(dc,0,0);
				if(oldcounter!=0) GetTextExtentPoint32(dc,(LPCTSTR)str,oldcounter,&size);
				else size.cx=0;
	
				rect.left=rect2.left+size.cx;

				SetTextJustification(dc,0,0);
				GetTextExtentPoint32(dc,(LPCTSTR)wrd,wrd.GetLength(),&size);
			
				rect.right=rect.left+size.cx;

				if(!IsBlank(wrd))
				{
					if ((id!=-1)&&(rect.left!=rect.right)) 
								 SaveList(id,name,
								 rect.left,rect.top,
								 rect.right,rect.bottom); 
				}
				
				if(wrd[0]!=' ') county+=1;
				str=str.Mid(counter+1);
				wrd=str;
				counter = 0;
				oldcounter=0;
			    newcounter=0;
			}
			
				

			if(oldcounter!=newcounter) 
			     wrd=str.Mid(oldcounter,newcounter-oldcounter+1);
		    else if(newcounter==0) wrd=str.Mid(oldcounter,counter-oldcounter);
			else wrd=str.Mid(oldcounter,counter-oldcounter+1);
			
			rect.top=rect2.top+county*tm.tmHeight;
			rect.bottom=rect2.top+(county+1)*tm.tmHeight;
	
			SetTextJustification(dc,0,0);
			if(oldcounter!=0) GetTextExtentPoint32(dc,(LPCTSTR)str,oldcounter,&size);
			else size.cx=0;

	
			rect.left=rect2.left+size.cx;

			SetTextJustification(dc,0,0);
			GetTextExtentPoint32(dc,(LPCTSTR)wrd,wrd.GetLength(),&size);

			rect.right=rect.left+size.cx;

			if(!IsBlank(wrd))
				{
					if ((id!=-1)&&(rect.left!=rect.right)) 
								 SaveList(id,name,
								 rect.left,rect.top,
								 rect.right,rect.bottom); 
				}
				

			
			if(newcounter==0) str=str.Mid(counter);
			else str=str.Mid(counter+1);
			wrd = str;
			counter=-1;
			oldcounter=0;
			newcounter=0;
			county+=1;

		}

		counter++;
	}
	
	
	SetTextJustification(dc,0,0);
	GetTextExtentPoint32(dc,(LPCTSTR)str,counter,&size);
			
	if(size.cx>rect2.right-rect2.left)
		{
			if(oldcounter!=newcounter) 
				wrd=str.Mid(oldcounter,newcounter-oldcounter+1);
	     	else if(newcounter==0) wrd=str.Mid(oldcounter,counter-oldcounter+1);
			else wrd=str.Mid(oldcounter,counter-newcounter+1);
				
			rect.top=rect2.top+county*tm.tmHeight;
			rect.bottom=rect2.top+(county+1)*tm.tmHeight;
			
			SetTextJustification(dc,0,0);
			if(oldcounter!=0) GetTextExtentPoint32(dc,(LPCTSTR)str,oldcounter,&size);
			else size.cx=0;
	
			rect.left=rect2.left+size.cx;
			SetTextJustification(dc,0,0);
			GetTextExtentPoint32(dc,(LPCTSTR)wrd,wrd.GetLength(),&size);

			rect.right=rect.left+size.cx;
		
			if(!IsBlank(wrd))
			{
				if ((id!=-1)&&(rect.left!=rect.right)) 
							 SaveList(id,name,
							 rect.left,rect.top,
							 rect.right,rect.bottom); 
			}

			if(newcounter==0) str=str.Mid(counter);
			else str=str.Mid(newcounter+1);

			wrd = str;
			county+=1;
		}	

				
	rect.top=rect2.top+county*tm.tmHeight;
	rect.bottom=rect2.top+(county+1)*tm.tmHeight;
			
	SetTextJustification(dc,0,0);
	if(oldcounter!=0) GetTextExtentPoint32(dc,(LPCTSTR)str,oldcounter,&size);
	else size.cx=0;
			
	wrd=str.Mid(oldcounter,counter-oldcounter+1);
			
	rect.left=rect2.left+size.cx;
			
	SetTextJustification(dc,0,0);
	GetTextExtentPoint32(dc,(LPCTSTR)wrd,wrd.GetLength(),&size);

	rect.right=rect.left+size.cx;

	if(!IsBlank(wrd))
		{
			if ((id!=-1)&&(rect.left!=rect.right)) 
						 SaveList(id,name,
						 rect.left,rect.top,
						 rect.right,rect.bottom); 
		}
	
	DeleteObject(SelectObject(dc, GetStockObject(SYSTEM_FONT)));
		
	ReleaseDC(hwnd,dc);

}




/*
FUNCTION : clearstring
ATTRIBUTES :
	CString str: The text of the window
NOTES:
	This function returns the text of the window whithout the 
symbols of the anchors.
*/


CString clearstring(CString str)
{
	CString tmp,tmp2;
	int x;
	BOOL flag=TRUE;

	tmp=str;
	tmp2.Empty();

	//ASSERT(0);
    
	while(flag)
	{
		x=tmp.Find('<');
		if(x!=-1)
		{
			if(IsAnchor(tmp))
			{
				tmp2+=tmp.Left(x);
				tmp=tmp.Mid(x);
				x=tmp.Find('>');
				tmp=tmp.Mid(x+1);
				//tmp2+=tmp;
				x=tmp.Find("</a>");
				if(x==-1) x=tmp.Find("</A>");
				if(x==-1) x=tmp.Find("<\\a>");
				if(x==-1) x=tmp.Find("<\\A>");
				
				tmp2+=tmp.Mid(0,x);
				
				tmp=tmp.Mid(x+4);
				//tmp2+=tmp;
				//tmp=tmp2;
				//tmp2.Empty();
			}
			else
			{	
				tmp2+=tmp.Left(x+1);
				tmp=tmp.Mid(x+1);
			}
		}
		else 
		{
			tmp2+=tmp;
			flag=FALSE;
		}
	}

	return tmp2;
}




/*
FUNCTION : puttext
ATTRIBUTES :
	HWND hwnd: The handler of the window
	char* str: The text of the window
	char* facename: The face name of the font in use.
	int size: Size of the font.
	int trasp: Is zero if we want to change the backround color of the window.
	COLORREF bkcolor: The new backround color of the window.
	COLORREF fontcolor: The font color
	CString align: A string that contains flags for the style 
				   of the text. It is empty if the text belongs 
				   to a text channel.
NOTES:
	This function displays the text of the window in the proper
area.
*/

void puttext(myWin* hwnd, char* str,char* facename,int size,int trasp,COLORREF bkcolor,COLORREF fontcolor,CString align,int x,int y)
{
	RECT rect;   
	HDC dc = ::GetDC(hwnd->m_hWnd);
	HFONT hfont;
	HBRUSH hbr;
	COLORREF color;
	CString tmp=str,bline;

	::GetClientRect(hwnd->m_hWnd,&rect);
	
	if(trasp==0)
	{
		SetBkMode(dc, TRANSPARENT);
		color = GetBkColor(dc);
		hbr = CreateSolidBrush(color);
		//FillRect(dc,&rect,hbr);
		DeleteObject(hbr);
	}
	else
	{
		SetBkMode(dc, TRANSPARENT);
		hbr = CreateSolidBrush(bkcolor);
		//FillRect(dc,&rect,hbr);
		DeleteObject(hbr);
	}
	
	color = GetTextColor(dc);
	SetTextColor(dc,fontcolor);

	if((x!=0)||(y!=0))
	{
		rect.left = x;
		rect.top = y;
	}
	else
	{
		bline = findmaxword(dc,tmp);
		findrect(dc,tmp,facename,size,bline,align,rect,rect);
		
		rect.top -= hwnd->m_nScrollPos;
	}

	hfont = EzCreateFont(dc, facename, size*10, 0, 0, TRUE);
	SelectObject(dc, hfont);
	DrawText(dc,str,-1,&rect,DT_LEFT|DT_WORDBREAK);
	DeleteObject(SelectObject(dc, GetStockObject(SYSTEM_FONT)));
	
	SetTextColor(dc,color);

	::ReleaseDC(hwnd->m_hWnd,dc);
	
}

//-------------------------------------------------

/*
FUNCTION : SaveList
ATTRIBUTES :
    int ID: The index of the callback function of the player
	CString anchor: The string index of the anchor 
	int x1,y1,x2,y2: The upper left and lower right corners of
					 in pixels, of the button of the anchor
NOTES:
	This function calls the proper player's function which creates
the list of the buttons for the anchors in the text.
*/	
    
void SaveList(int ID,CString anchor,int x1,int y1,int x2,int y2)
{
	PyObject *callback, *callbackArgs, *result, *callID;

	if (CallbackMap)
	{
		callID = Py_BuildValue ("i", (int) ID);
		
		// is this timer id recognized?
		callback = PyDict_GetItem (CallbackMap, callID);

		// call the user's function
		if (callback)
		{
			//Argument List Must Be a Tuple!!!
			callbackArgs = Py_BuildValue ("(iiiis)", x1, y1, x2, y2, (LPCTSTR)anchor);
			result = PyEval_CallObject (callback, callbackArgs);
			if (!result)
			{
				// Is this necessary, or will python already have flagged
				// an exception?  Can we even catch exceptions here?
				PyErr_Print();
			}
			// everything's ok, return
			Py_XDECREF(callbackArgs);
			Py_XDECREF(result);
			Py_DECREF (callID);
			return;
		}
	}
}


//
static PyObject* py_example_PutText(PyObject *self, PyObject *args)
{
	char *bit,*ch,*facename,*align;
	int size,id,bktrasp,bkred,bkblue,bkgreen,fred,fblue,fgreen,x,y;
	myWin *obWnd;
	CString tmp,algn;
	PyObject *testOb = Py_None;
	COLORREF bkcolor,fontcolor;

	
	if(!PyArg_ParseTuple(args, "iOssii(iii)(iii)s(ii)", &id, &testOb, &bit, &facename, &size, 
		                                       &bktrasp, &bkred, &bkgreen, &bkblue, 
											   &fred, &fgreen, &fblue, &align, &x, &y))
		return NULL;
	
	obWnd = GetMyWndPtr(testOb);
	ASSERT(obWnd != NULL);
	if (obWnd==NULL) return NULL;
	
	algn = align;

	tmp=clearstring(bit);

	bkcolor = RGB(bkred,bkgreen,bkblue);
	fontcolor = RGB(fred,fgreen,fblue);

	ch=new char[strlen(tmp)+1];
	strcpy(ch, tmp);
	
	puttext(obWnd,ch,facename,size,bktrasp,bkcolor,fontcolor,algn,x,y);

	delete ch;

	Py_INCREF(Py_None);
	return Py_None;

}




static PyObject* py_example_PrepareText(PyObject *self, PyObject *args)
{
	CFile f;
	myWin *obWnd;
	PyObject *testOb = Py_None;
	char *filename, *bit, *facename,*algn;
	PyObject *tmp,*callback,*callbackID;
	DWORD cnumber;
	CString str,align;
	static int ID=0;
	BOOL inputType=FALSE; //FALSE: String, TRUE: Filename
	int id, size;
		
	if(!PyArg_ParseTuple(args, "OOisisis", &testOb, &callback, &id, &filename, &inputType, &facename, &size, &algn))
		return NULL;
	
	align = algn;
	
	if(id==-1)
	{
		// make sure the callback is a valid callable object
		if (!PyCallable_Check (callback))
			return CmifExErrorFunc("Bad callback function");

		callbackID = Py_BuildValue ("i", (int)ID);

		// associate the timer id with the given callback function
		if (PyObject_SetItem (CallbackMap, callbackID, callback) == -1)
			return NULL;
		
		id=ID;
		ID++;
	}

	if(inputType)
	{
		if(!f.Open(filename, CFile::modeRead, NULL))
			return CmifExErrorFunc("Cannot open the file");
		else
		{	
			cnumber = f.GetLength();//-sizeof(EOF);
			bit = new char[cnumber+1];
			f.Read(bit, cnumber);
			bit[cnumber] = 0;
			f.Close();	
		}
	}
	else
	{
		bit = new char[strlen(filename)+1];
		strcpy(bit,filename);
	}
    
    		
	if(bit!=NULL)
	{
		str=bit;
		//str=clearstring(str);
		str = expandtabs(str,align);
		obWnd = GetMyWndPtr(testOb);
		ASSERT_VALID(obWnd);
		obWnd->GetDim(align,facename,size);
		//if (align.IsEmpty()) obWnd->SetScroll(str);
		//obWnd->align = align;
		GetAnchorList(obWnd, str,facename,size,id,align);
		//if (align.IsEmpty()) obWnd->SetScroll("");
		//obWnd->align = align;
		tmp=Py_BuildValue("is", id, (LPCTSTR)str);
		delete bit;
		return tmp;
	}
	else
		return CmifExErrorFunc("NULL string");

	Py_INCREF(Py_None);
	return Py_None;	
}


static PyObject* py_example_GetScrollPos(PyObject *self, PyObject *args)
{
	myWin *obWnd;
	PyObject *testOb = Py_None, *tmp;
	
	if(!PyArg_ParseTuple(args, "O", &testOb))
		return NULL;

	obWnd =GetMyWndPtr(testOb);
	
	if(obWnd->single_anchor) obWnd->difer = 0;
	tmp=Py_BuildValue("i", obWnd->difer);

	return tmp;
}



static PyObject* py_example_SetScrollPos(PyObject *self, PyObject *args)
{
	myWin *obWnd;
	PyObject *testOb = Py_None;//, *tmp;
	char *s;
	CString str;
	
	if(!PyArg_ParseTuple(args, "Os", &testOb, &s))
		return NULL;

	str = s;
	obWnd = GetMyWndPtr(testOb);
	
	obWnd->SetScroll(str);

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* py_example_ClearXY(PyObject *self, PyObject *args)
{
	myWin *obWnd;
	PyObject *testOb = Py_None;
	
	if(!PyArg_ParseTuple(args, "O", &testOb))
		return NULL;

	obWnd = GetMyWndPtr(testOb);
	
	obWnd->difer = 0;
		
	return Py_None;
}
// 
// End of TEXTEX stuff
///////////////////////////////////////////////////////////////


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

	// Textex functions
	{ "PutText", (PyCFunction)py_example_PutText, 1},
    { "PrepareText", (PyCFunction)py_example_PrepareText, 1},
	{ "GetScrollPos", (PyCFunction)py_example_GetScrollPos, 1},
	{ "SetScrollPos", (PyCFunction)py_example_SetScrollPos, 1},
	{ "ClearXY", (PyCFunction)py_example_ClearXY, 1},


	{ NULL, NULL }
};

extern "C" __declspec(dllexport) 
void initcmifex()
{
	PyObject *m, *d;
	m = Py_InitModule("cmifex", CmifExMethods);
	d = PyModule_GetDict(m);
	CmifExError = PyString_FromString("cmifex.error");
	PyDict_SetItemString(d, "error", CmifExError);
	CallbackMap = PyDict_New();
}


