// ContainerWnd.cpp : implementation file
//
#include "stdafx.h"

//#include "htmlex.h"
#include "moddef.h"

#include "ContainerWnd.h"

#include "string.h"
#include "stdio.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#undef THIS_FILE
static char THIS_FILE[] = __FILE__;
#endif

#define IDC_HTMLCTRL 101 // resource-id (for html control)
#define LIM			 500 //bytes- lower limit of document to be retrieved 
						 // for statistics to be displayed	  
#define ARROW_CURSOR   0
#define WAIT_CURSOR	   1
	 

//CHTMLForms collection;
//CHTMLForm form;
int count = 0;
int count1 =0;


extern PyObject *CallbackMap;

//////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////
/////////////////////// Callable Function /////////////////////////////////
///////// in this case returns the fired cmif link to cmif/////////////////
///////////////////////////////////////////////////////////////////////////

void CallPyFunction(const char* value, int ID)
{
	PyObject *callID, *callback, *callbackArgs, *result;

	if (CallbackMap)
	{
		callID = Py_BuildValue ("i", (int) ID);
	
		// is this timer id recognized?
		callback = PyDict_GetItem (CallbackMap, callID);

		// call the user's function
		if (callback)
		{
			//Argument List Must Be a Tuple!!!
			callbackArgs = Py_BuildValue ("(s)", value);
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


	



/////////////////////////////////////////////////////////////////////////////
// CContainerWnd

CContainerWnd::CContainerWnd()
{
	TRACE("Container wnd constructor\n");
	char empty[] = "\n\n\n";
	m_Status = NULL;
	m_ctrl_cr = FALSE;
	m_id = -1;
	m_title = "";
	m_bCmifHit = FALSE;
	m_strPath ="";
	m_newurl = "";
	m_bfurl = TRUE;
	m_bnewReq = FALSE;
	m_pMemDC = new CDC;
	m_pBitmap = new CBitmap;
	m_count = 0;
	m_url_current="";
}

CContainerWnd::~CContainerWnd()
{
	delete m_pMemDC;
	delete m_pBitmap;
}


BEGIN_MESSAGE_MAP(CContainerWnd, CWnd)
	ON_MESSAGE(WM_RETRIEVE, OnRetrieve)
	//{{AFX_MSG_MAP(CContainerWnd)
	ON_WM_SIZE()
	ON_WM_MOUSEMOVE()
	//ON_WM_PAINT()
	//ON_WM_CONTEXTMENU()
	//ON_WM_CHAR()
	//}}AFX_MSG_MAP
END_MESSAGE_MAP()


/////////////////////////////////////////////////////////////////////////////
// CContainerWnd message handlers


BEGIN_EVENTSINK_MAP(CContainerWnd, CWnd)
    //{{AFX_EVENTSINK_MAP(CContainerWnd)
	ON_EVENT(CContainerWnd, IDC_HTMLCTRL, 106 /* DownloadBegin */, OnDownloadBegin, VTS_NONE)
	ON_EVENT(CContainerWnd, IDC_HTMLCTRL, 104 /* DownloadComplete */, OnDownloadComplete, VTS_NONE)
	ON_EVENT(CContainerWnd, IDC_HTMLCTRL, 102 /* StatusTextChange */, OnStatusTextChange, VTS_BSTR)
	ON_EVENT(CContainerWnd, IDC_HTMLCTRL, 113 /* TitleChange */, OnTitleChange, VTS_BSTR)
	ON_EVENT(CContainerWnd, IDC_HTMLCTRL, 107 /* NewWindow */, OnNewWindow, VTS_BSTR VTS_I4 VTS_BSTR VTS_PVARIANT VTS_BSTR VTS_PBOOL)
	ON_EVENT(CContainerWnd, IDC_HTMLCTRL, 100 /* BeforeNavigate */, OnBeforeNavigate, VTS_BSTR VTS_I4 VTS_BSTR VTS_PVARIANT VTS_BSTR VTS_PBOOL)
	ON_EVENT(CContainerWnd, IDC_HTMLCTRL, 101 /* NavigateComplete */, OnNavigateComplete, VTS_BSTR)
	ON_EVENT(CContainerWnd, IDC_HTMLCTRL, 108 /* ProgressChange */, OnProgressChange, VTS_I4 VTS_I4)
	ON_EVENT(CContainerWnd, IDC_HTMLCTRL, 103 /* Quit */, OnQuit, VTS_PBOOL)
	//}}AFX_EVENTSINK_MAP
END_EVENTSINK_MAP()


void CContainerWnd::OnProgressChange(long Progress, long ProgressMax) 
{
	// TODO: Add your control notification handler code here
	
}

void CContainerWnd::OnQuit(BOOL FAR* Cancel) 
{
	// TODO: Add your control notification handler code here
	
}



void CContainerWnd::OnDownloadBegin() 
{
	// TODO: Add your control notification handler code here
	
}

void CContainerWnd::OnDownloadComplete() 
{
	// TODO: Add your control notification handler code here
	
}


void CContainerWnd::OnNewWindow(LPCTSTR URL, long Flags, LPCTSTR TargetFrameName, VARIANT FAR* PostData, LPCTSTR Headers, BOOL FAR* Processed) 
{
	*Processed = TRUE;
}

void CContainerWnd::OnStatusTextChange(LPCTSTR Text) 
{
	if (m_Status != NULL)     
	 ::SetWindowText(m_Status, Text);
}

void CContainerWnd::OnBeforeNavigate(LPCTSTR URL, long Flags, LPCTSTR TargetFrameName, VARIANT FAR* PostData, LPCTSTR Headers, BOOL FAR* Cancel) 
{

	CString str1, str;
	char comp[] = "cmif:";
	char cmif[256]="";
	char path[256]="";
	char storestr[256]="";
	UINT index;

	CString url((LPCTSTR) URL);

	CWaitCursor wait;
	if (strstr(URL, comp)!= NULL)
	{
		index = url.ReverseFind(':');
		url = url.Mid(index+1);
		m_url_current = url;
		CallPyFunction((LPCTSTR)url, m_id);
		m_bCmifHit = TRUE;
		*Cancel=TRUE;
		return;

	 }	

	m_url_current = URL;
}

void CContainerWnd::OnNavigateComplete(LPCTSTR URL) 
{
	
}

void CContainerWnd::OnTitleChange(LPCTSTR Text) 
{
}
void CContainerWnd::Retrieve(const char* url)
{
	m_html.Navigate(url,NULL,NULL,NULL,NULL);
}

LONG CContainerWnd::OnRetrieve(UINT wParam, LONG lParam) 
{
	return 0L;
}


void CContainerWnd::UpdateWnd()
{
	CPaintDC dc(this); // device context for painting
	CRect rc;
	dc.GetClipBox(&rc);
	// Update memory dc with Gray background and DIB
	if (m_pMemDC->GetSafeHdc() == NULL) {
		m_pMemDC->CreateCompatibleDC(&dc);
		m_pBitmap->CreateCompatibleBitmap(&dc, 1024, 768);
	}
	CBitmap* pOld = m_pMemDC->SelectObject(m_pBitmap);
	m_pMemDC->SelectClipRgn(NULL);
	m_pMemDC->IntersectClipRect(&rc);
	m_pMemDC->SelectStockObject(GRAY_BRUSH);
	m_pMemDC->Rectangle(rc);
	//	DisplayDib(m_pMemDC->GetSafeHdc());
		
	// BitBlt to Display dc
	dc.BitBlt(rc.left, rc.top, rc.Width(), rc.Height(), 
				m_pMemDC, rc.left, rc.top, SRCCOPY);

	m_pMemDC->SelectObject(pOld);
}

void CContainerWnd::MoveWnd()
{
	CRect rc;

	if (m_ctrl_cr)
	{
		
		GetClientRect(&rc);	
		m_html.MoveWindow(&rc, TRUE);
	}
}

void CContainerWnd::OnSize(UINT nType, int cx, int cy) 
{
	CRect rc;
	int st_bar_h;

	CWaitCursor wait;

	if (m_ctrl_cr)
	{
		GetClientRect(&rc);
		if(m_Status!=NULL)
		{
			st_bar_h = ::GetSystemMetrics(SM_CYCAPTION)+1;
			rc.DeflateRect(0,0,0,st_bar_h);
		}
		m_html.MoveWindow(&rc, TRUE);
	}
	
	
}


void CContainerWnd::OnMouseMove(UINT nFlags, CPoint point) 
{
	
	if (m_cursor_type == WAIT_CURSOR)
			SetCursor(LoadCursor(NULL, IDC_WAIT));
	if (m_cursor_type == ARROW_CURSOR)
			SetCursor(LoadCursor(NULL, IDC_ARROW));
	CWnd::OnMouseMove(nFlags, point);
}

void CContainerWnd::OnPaint() 
{
	UpdateWnd();
}

void CContainerWnd::OnContextMenu(CWnd* pWnd, CPoint point) 
{
}

void CContainerWnd::OnChar(UINT nChar, UINT nRepCnt, UINT nFlags) 
{
	
	CWnd::OnChar(nChar, nRepCnt, nFlags);
}
