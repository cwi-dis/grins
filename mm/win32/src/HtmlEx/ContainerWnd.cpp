// ContainerWnd.cpp : implementation file
//


#include "stdafx.h"
#include "htmlex.h"
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

#ifdef __cplusplus
extern "C" {
#endif

void CallableFunction(const char* value, int ID)
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


	
#ifdef __cplusplus
}
#endif



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
	//ON_EVENT(CContainerWnd, IDC_HTMLCTRL, 4 /* BeginRetrieval */, OnBeginRetrievalHtml, VTS_NONE)
	//ON_EVENT(CContainerWnd, IDC_HTMLCTRL, 6 /* EndRetrieval */, OnEndRetrievalHtml, VTS_NONE)
	//ON_EVENT(CContainerWnd, IDC_HTMLCTRL, 7 /* DoRequestDoc */, OnDoRequestDocHtml, VTS_BSTR VTS_DISPATCH VTS_DISPATCH VTS_PBOOL)
	//ON_EVENT(CContainerWnd, IDC_HTMLCTRL, 1 /* ParseComplete */, OnParseCompleteHtml, VTS_NONE)
	//ON_EVENT(CContainerWnd, IDC_HTMLCTRL, 2 /* LayoutComplete */, OnLayoutCompleteHtml, VTS_NONE)
	//ON_EVENT(CContainerWnd, IDC_HTMLCTRL, -608 /* Error */, OnErrorHtml, VTS_I2 VTS_PBSTR VTS_I4 VTS_BSTR VTS_BSTR VTS_I4 VTS_PBOOL)
	//ON_EVENT(CContainerWnd, IDC_HTMLCTRL, 5 /* UpdateRetrieval */, OnUpdateRetrievalHtml, VTS_NONE)
	//ON_EVENT(CContainerWnd, IDC_HTMLCTRL, 9 /* DoRequestSubmit */, OnDoRequestSubmitHtml, VTS_BSTR VTS_DISPATCH VTS_DISPATCH VTS_PBOOL)
	//ON_EVENT(CContainerWnd, IDC_HTMLCTRL, 551 /* Timeout */, OnTimeoutHtml, VTS_NONE)
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
	// TODO: Add your control notification handler code here
	//CString tmp, tmp2;
	//tmp = m_html.GetDocument();
	//tmp2 = m_html.GetLocationURL();
	//m_html.Stop();
	//m_html.Navigate((LPCTSTR)m_html.GetLocationURL(),NULL,(VARIANT*)TargetFrameName,NULL,NULL);
	*Processed = TRUE;
}

void CContainerWnd::OnStatusTextChange(LPCTSTR Text) 
{
	// TODO: Add your control notification handler code here
	//AfxMessageBox(Text, MB_OK);
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

	//m_url_current = (LPCTSTR)URL;
	//AfxMessageBox(URL, MB_OK);

	CWaitCursor wait;
	if (strstr(URL, comp)!= NULL)
	{
		//AfxMessageBox("Cmif link!", MB_OK);
		
		//for(UINT i=0; (URL[i]!='\0' && i<256); i++)
		//	count = i;

		//for(i=count; (URL[i]!=':' && i>0); i--)
		//	index = i;

		//for(i=0; (URL[i]!='\0' && i<256); i++)
		//	cmif[i] = URL[i+index];	// hack to obtain a string without
									// the beginning:  file://localhost/...../cmif: 
		//AfxMessageBox(cmif, MB_OK);
		index = url.ReverseFind(':');
		url = url.Mid(index+1);
		m_url_current = url;
		CallableFunction((LPCTSTR)url, m_id);
		m_bCmifHit = TRUE;
		*Cancel=TRUE;
		return;

	 }	

	 
	m_url_current = URL;
	

	//display status bar messages

	 //str1.Format("Contacting : %s", URL);
	 //str = m_title + " :: " + str1;


	 //if the window has a status bar created, display text there
	 //if (m_Status != NULL)     
	 //::SetWindowText(m_Status, (LPCTSTR) str);
}

void CContainerWnd::OnNavigateComplete(LPCTSTR URL) 
{
	// TODO: Add your control notification handler code here
	
}

void CContainerWnd::OnTitleChange(LPCTSTR Text) 
{
	// TODO: Add your control notification handler code here
	//AfxMessageBox(Text, MB_OK);
}

/*void CContainerWnd::OnBeginRetrievalHtml()
{
	if (m_Status != NULL)
		::SetWindowText(m_Status, m_title + " :: " + "Document retrieval begins...");

}

void CContainerWnd::OnEndRetrievalHtml()
{
	
}*/

//void CContainerWnd::OnDoRequestDocHtml(LPCTSTR URL, LPDISPATCH Element, LPDISPATCH DocInput, BOOL FAR* EnableDefault)
//{
//	CString str1, str;
//	char comp[] = "cmif:";
//	char cmif[256]="";
//	char path[256]="";
//	char storestr[256]="";
//	char path1[256];
//	UINT count, index;
//
//	CString url((LPCTSTR) URL);
//
//	m_url_current = (LPCTSTR)URL;
//
//	//AfxMessageBox(URL, MB_OK);
//
//	CWaitCursor wait;
//	if (strstr(URL, comp)!= NULL)
//	{
//		//AfxMessageBox("Cmif link!", MB_OK);
//		
//		for(UINT i=0; (URL[i]!='\0' && i<256); i++)
//			count = i;
//
//		for(i=count; (URL[i]!=':' && i>0); i--)
//			index = i;
//
//		for(i=0; (URL[i]!='\0' && i<256); i++)
//			cmif[i] = URL[i+index];	// hack to obtain a string without
//									// the beginning:  file://localhost/...../cmif: 
//		//AfxMessageBox(cmif, MB_OK);
//		CallableFunction(cmif, m_id);
//		m_bCmifHit = TRUE;
//		return;
//
//	 }	
//
//	 
//	
//	if ((!m_bfurl) && (url.Find("http:") == -1))
//	{
//		
//	// check the possibility of a request for a file that exists 
//	// in the current directory
//	// the OCX control does not search there, so a
//	// url error might be generated
//		if ((url.Find("|")== -1) )
//		{
//			//AfxMessageBox("Not a first URL", MB_OK);
//			for(UINT j=0; (URL[j]!='\0' && j<256); j++)
//			path1[j] = URL[j+17];    //exclude (file://localhost)
//		
//			CString temp3(path1);
//
//			
//			CString store = "file:///" + m_strPath + temp3;
//			
//			m_bnewReq = TRUE;  //error handler will handle the situation
//		
//			m_newurl = store;
//
//			return;
//		}
//	}
//	
//	
//
//	if ((url.Find("//www") == -1) && (url.Find("http:") == -1))
//	{
//		
//		for(UINT j=0; (URL[j]!='\0' && j<256); j++)
//			path[j] = URL[j+17];    //store full path except file://localhost
//		 
//				
//		// store the path without the filename
//		int len = strlen(path);
//
//		CString help = CString("\\");
//		char c = help.GetAt(0);     // c is the newline character
//
//		while (!(path[len-1] == '/'))
//			len--;
//
//		for (int k=0; k<len; k++)
//			storestr[k] = path[k];
//
//
//		CString newpath(storestr);
//		m_strPath = newpath;		
//
//		//AfxMessageBox(m_strPath, MB_OK);
//	}
//
//	//display status bar messages
//
//	 str1.Format("Contacting : %s", URL);
//	 str = m_title + " :: " + str1;
//
//
//	 //if the window has a status bar created, display text there
//	 if (m_Status != NULL)     
//	 ::SetWindowText(m_Status, (LPCTSTR) str);
//			
//	 //else check if a parent with a status bar exists
//	 /*else
//	 {
//		CContainerWnd* Parent = (CContainerWnd*) GetParent();
//		if (Parent != NULL) 
//		{
//			if (Parent->m_Status != NULL)
//			::SetWindowText(Parent->m_Status, (LPCTSTR) str);
//		}
//	 }*/
//	 
//}		


//void CContainerWnd::OnParseCompleteHtml() 
//{
//	//if the window has a status bar created, display text there
//	if (m_Status != NULL)
//	::SetWindowText(m_Status, m_title + " :: Document parsing complete...");
//	//else check if a parent with a status bar exists
//	/*else
//	{
//		CContainerWnd* Parent = (CContainerWnd*) GetParent();
//		if (Parent != NULL) 
//		{
//			if (Parent->m_Status != NULL)
//				::SetWindowText(Parent->m_Status,
//							m_title + " :: Document parsing complete...");
//		}
//	 }*/	
//}


//void CContainerWnd::OnLayoutCompleteHtml() 
//{	
//
//	if (m_bfurl)			
//		 m_bfurl = FALSE;   //not first url any more
//	
//	//if the window has a status bar created, display text there
//	if (m_Status != NULL)
//	::SetWindowText(m_Status, m_title + " :: Document Layout retrieval completed...");
//	//else check if a parent with a status bar exists
//	/*else
//	{
//		CContainerWnd* Parent = (CContainerWnd*) GetParent();
//		if (Parent != NULL) 
//		{
//			if (Parent->m_Status != NULL)
//			::SetWindowText(Parent->m_Status, 
//						m_title + " :: Document Layout retrieval completed...");
//		}
//	 }*/	
//	
//}


//void CContainerWnd::OnErrorHtml(short Number, BSTR FAR* Description, long Scode, LPCTSTR Source, LPCTSTR HelpFile, long HelpContext, BOOL FAR* CancelDisplay) 
//{
//	CString str1, str2, str3, str;
//
//	if (m_bnewReq)	// error due to inability to satisfy request in the same folder
//	{
//		m_bnewReq = FALSE;
//		//PostMessage(WM_RETRIEVE);
//		return;
//	}
//
//	if (m_bCmifHit)   //just a cmif link - do not indicate any error
//	{
//		m_bCmifHit = FALSE;
//		return;
//	}
//	
//	str1.Format("Problem contacting the specified URL\n");
//	str2.Format("The server may be down or not responding\n");
//	str3.Format("Check that the correct URL is given and try again\n");
//	str = str1 + str2 + str3;
//
//	//AfxMessageBox(str, MB_OK);
//
//	//if the window has a status bar created, display text there
//	if (m_Status != NULL)
//	::SetWindowText(m_Status, 
//						m_title + " :: Error while contacting the specified URL");
//	//else check if a parent with a status bar exists
//	/*else
//	{
//		CContainerWnd* Parent = (CContainerWnd*) GetParent();
//		if (Parent != NULL) 
//		{
//			if (Parent->m_Status != NULL)
//			::SetWindowText(Parent->m_Status,
//						m_title + " :: Error while contacting the specified URL");
//		}
//	 }*/	
//		
//}


//void CContainerWnd::OnUpdateRetrievalHtml() 
//{
//	LONG Total, Done;
//	int	Per;
//	CString str1, str2, str3, str4, str5, str;
//	CString strdone = m_title +" :: " + "Done";
//
//	//Total = m_html.GetRetrieveBytesTotal();
//	//Done  = m_html.GetRetrieveBytesDone();
//	//if (Total > LIM)
//	//Per = ((Done/Total))*100;
//
//	
//	//str1.Format("    %d       ",Per);
//	//str2.Format("     of ");
//	//str3.Format("   %d K", Total/1024);
//	
//	//if(Per>101)   //no more than 100%
//	//	return;
//
//	//if(Per)
//	//str4 = str1 + "%" + str2 + str3;
//	//else
//	//str4 =  str3 + " (total) ";
//
//	//append title and proper indication
//	//str = m_title +" :: " + "Transfering Data..." + str4; 
//																	
//	
//		
//
//	//if the window has a status bar created, display text there
//	//if (m_Status != NULL){
//	//	::SetWindowText(m_Status, (LPCTSTR)str);
//	//	if (Per == 100)
//	//	::SetWindowText(m_Status, (LPCTSTR)strdone);
//	//}
//	//else check if a parent with a status bar exists
//	/*else
//	{
//		CContainerWnd* Parent = (CContainerWnd*) GetParent();
//		if (Parent != NULL) 
//		{
//			if (Parent->m_Status != NULL){
//				::SetWindowText(Parent->m_Status, (LPCTSTR)str);
//				if (Per == 100)
//				::SetWindowText(Parent->m_Status, (LPCTSTR)strdone);
//			}
//		}
//	 }*/	
//	
//	
//}


void CContainerWnd::Retrieve(const char* url)
{
	m_html.Navigate(url,NULL,NULL,NULL,NULL);
}



LONG CContainerWnd::OnRetrieve(UINT wParam, LONG lParam) 
{
	//AfxMessageBox("RERETRIEVAL", MB_OK);
	//m_html.RequestDoc((LPCTSTR)m_url_current);
	//Retrieve((LPCTSTR)m_newurl);
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
	
	/*if (count<8)
	{
		AfxMessageBox("Mouse Move", MB_OK);
		count++;
	}*/
	if (m_cursor_type == WAIT_CURSOR)
			//RestoreWaitCursor();
			SetCursor(LoadCursor(NULL, IDC_WAIT));
	if (m_cursor_type == ARROW_CURSOR)
			SetCursor(LoadCursor(NULL, IDC_ARROW));
	CWnd::OnMouseMove(nFlags, point);
}

void CContainerWnd::OnPaint() 
{
	//CPaintDC dc(this); // device context for painting
	
	UpdateWnd();
	
	// Do not call CWnd::OnPaint() for painting messages
}

void CContainerWnd::OnContextMenu(CWnd* pWnd, CPoint point) 
{
	//collection = m_html.GetForms();	
	//long res = collection.GetCount();
	//int r = (int) res;
	//BYTE b =1;
	//COleVariant vr(b);
	//form = collection.Item(vr.Detach());
	//form.RequestSubmit();
	//CString str;
	//str.Format("NumOfForms: %d\n", r);
	//AfxMessageBox(str, MB_OK);	
}


/*void CContainerWnd::OnDoRequestSubmitHtml(LPCTSTR URL, LPDISPATCH Form, LPDISPATCH DocOutput, BOOL FAR* EnableDefault) 
{
	//AfxMessageBox("Request for form submission", MB_OK);
	//AfxMessageBox(URL, MB_OK);
	//EnableDefault = TRUE;
	CString str, cancel_str;
	UINT len;

	cancel_str = URL;
	//COleVariant vr1((LPCTSTR)cancel_str);
	m_html.Stop();	

	//collection = m_html.GetForms();	
	//long res = collection.GetCount();
	//int r = (int) res;
	//BYTE b = 1;					//the first form!
	//COleVariant vr(b);
	//form = collection.Item(vr.Detach());
	//CString tmp = form.GetURLEncodedBody();
	//AfxMessageBox(tmp, MB_OK);	
	//form.RequestSubmit();
	//str.Format("NumOfForms: %d\n", r);
	//AfxMessageBox(str, MB_OK);	
	//m_html.RequestDoc("file://localhost/D|/tmp/quering.htm");

	//char* temp;

	// submission of a query takes place
	
	//len = tmp.GetLength();

	//LPCTSTR content = (LPCTSTR) tmp;

	//temp = new char[len+1];
	//for (UINT l=0; l<len; l++)
	//	temp[l] = '\0';
	

	//for (l=0; l<len; l++)
	//	temp[l] = content[l];
	//temp[len]='&';
	
	//AfxMessageBox(temp, MB_OK);	

	//CallableFunction(temp, m_id);

	//m_html.RequestDoc(URL);
	
}

void CContainerWnd::OnTimeoutHtml() 
{
	AfxMessageBox("TimeOut Occured", MB_OK);
	
}*/

void CContainerWnd::OnChar(UINT nChar, UINT nRepCnt, UINT nFlags) 
{
	
	CWnd::OnChar(nChar, nRepCnt, nFlags);
}
