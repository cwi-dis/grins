#include "stdafx.h"

#include "win32win.h"
#include "win32uiExt.h"

#include <afxdisp.h>
#include <exdisp.h>

// IE_CONTROL (0)
#include "webbrowser2.h"

// WEBSTER_CONTROL (1)
#include "websterpro.h"
// leave it as text?
static CString strLicKey("Webster Pro - Copyright (c) 1995-1998 Home Page Software Inc. - A Webster CodeBase Product"); 
static BSTR bstrLicKey=strLicKey.AllocSysString(); 

// the c++/mfc class 
class CHtmlWnd: public CWnd
	{
	protected:
	DECLARE_DYNCREATE(CHtmlWnd)
	DECLARE_EVENTSINK_MAP()
	DECLARE_MESSAGE_MAP()

	public:
	CHtmlWnd():m_selHtmlCtrl(0),m_bCtrlCreated(false),m_isclient(false){}
	virtual ~CHtmlWnd(){}
	virtual BOOL Create(LPCTSTR lpszClassName, LPCTSTR lpszWindowName,
		DWORD dwStyle, const RECT& rect, CWnd* pParentWnd, UINT nID,
		CCreateContext* pContext = NULL);
	
	// Browser Control Selection
	void UseHtmlCtrl(int selControl){m_selHtmlCtrl=selControl;}
	void UseIECtrl(){m_selHtmlCtrl=IE_CONTROL;}
	void UseWebsterCtrl(){m_selHtmlCtrl=WEBSTER_CONTROL;}
	int m_selHtmlCtrl;
	enum {IE_CONTROL=0,WEBSTER_CONTROL=1};


	// Control creation
	BOOL CreateHtmlCtrl();
	void DestroyHtmlCtrl();
	bool HasHtmlCtrl(){return m_bCtrlCreated;}

	// Operations
	public:
	void Navigate(LPCTSTR lpszURL);
	void SetImmHtml(LPCTSTR str);
	void Refresh();
	void SetBackColor(COLORREF clr);

	// Dim helpers
	void SetClient(bool b){m_isclient=b;}
	void FitHtmlCtrl();
	// custom url support
	LPCTSTR GetForeignUrl(){return m_foreignUrl;}
	CString m_foreignUrl;


	private:
	void CheckForCustomURL(LPCTSTR pszURL,BOOL* bCancel);
	CWebBrowser2 m_wndWebBrowser;
	CWebsterPro  m_wndWebsterBrowser;
	bool m_isclient;
	bool m_bCtrlCreated;

	// Generated message map functions
	protected:
	//{{AFX_MSG(CHtmlWnd)
	afx_msg void OnSize(UINT nType, int cx, int cy);
	afx_msg void OnPaint();
	afx_msg void OnDestroy();
	// IE
	afx_msg void OnBeforeNavigateIE(LPDISPATCH pDisp, VARIANT FAR* URL, VARIANT FAR* Flags, VARIANT FAR* TargetFrameName, VARIANT FAR* PostData, VARIANT FAR* Headers, BOOL FAR* Cancel);
	// Webster
	afx_msg void OnBeforeNavigateWebster(BSTR FAR* URL, long mFlags, long nHandle, BSTR FAR* TargetName, BSTR FAR* ExtraHeaders, BSTR FAR* TextToPost, BOOL FAR* Cancel);
	//}}AFX_MSG
	};

///////////////////////////////////////////////
//   IMPLEMENTATION

IMPLEMENT_DYNCREATE(CHtmlWnd, CWnd)

BEGIN_MESSAGE_MAP(CHtmlWnd, CWnd)
	//{{AFX_MSG_MAP(CHtmlView)
	ON_WM_SIZE()
	ON_WM_PAINT()
	ON_WM_DESTROY()
	//}}AFX_MSG_MAP
END_MESSAGE_MAP()

BEGIN_EVENTSINK_MAP(CHtmlWnd, CWnd)
    //{{AFX_EVENTSINK_MAP(CContainerWnd)
	ON_EVENT(CHtmlWnd, AFX_IDW_PANE_FIRST, 250 /* BeforeNavigate2 */, OnBeforeNavigateIE, VTS_DISPATCH VTS_PVARIANT VTS_PVARIANT VTS_PVARIANT VTS_PVARIANT VTS_PVARIANT VTS_PBOOL)
	ON_EVENT(CHtmlWnd, AFX_IDW_PANE_FIRST, 12 /* BeforeNavigate */, OnBeforeNavigateWebster, VTS_PBSTR VTS_I4 VTS_I4 VTS_PBSTR VTS_PBSTR VTS_PBSTR VTS_PBOOL)
	//}}AFX_EVENTSINK_MAP
END_EVENTSINK_MAP()

void CHtmlWnd::OnDestroy()
	{
	m_bCtrlCreated=false;
	}

void CHtmlWnd::OnSize(UINT nType, int cx, int cy)
	{
	CWnd::OnSize(nType, cx, cy);
	FitHtmlCtrl();
	}

void CHtmlWnd::OnPaint()
	{
	Default();
	}

void CHtmlWnd::OnBeforeNavigateWebster(BSTR FAR* URL, long mFlags, long nHandle, 
	BSTR FAR* TargetName, BSTR FAR* ExtraHeaders, BSTR FAR* TextToPost, BOOL FAR* Cancel)
	{
	CString strURL(*URL);
	CheckForCustomURL(strURL,Cancel);
	}

void CHtmlWnd::OnBeforeNavigateIE(
	LPDISPATCH pDisp, 
	VARIANT FAR* URL, 
	VARIANT FAR* Flags, 
	VARIANT FAR* TargetFrameName, 
	VARIANT FAR* PostData, 
	VARIANT FAR* Headers, 
	BOOL FAR* Cancel) 
	{
	CString strURL((BSTR)URL->bstrVal);
	CheckForCustomURL(strURL,Cancel);
	}

void CHtmlWnd::CheckForCustomURL(LPCTSTR pszURL,BOOL* bCancel)
	{
	// default is to continue
	*bCancel = FALSE;

	// check for foreign format
	CString url(pszURL);
	CString prefix= "cmif:";
	if (url.Find(prefix)!=-1)
		{
		m_foreignUrl=url;
		PostMessage(WM_USER); // notify user to get it
		*bCancel=TRUE;
		}	
	}

/////////////////////////////////////////////////////////////////////////////
// CHtmlWnd operations

BOOL CHtmlWnd::Create(LPCTSTR lpszClassName, LPCTSTR lpszWindowName,
						DWORD dwStyle, const RECT& rect, CWnd* pParentWnd,
						UINT nID, CCreateContext* pContext)
	{
	if (!CWnd::Create(lpszClassName, lpszWindowName,
		dwStyle, rect, pParentWnd,  nID, pContext))
		return FALSE;
	return TRUE;
	}

BOOL CHtmlWnd::CreateHtmlCtrl()
	{
	if(m_bCtrlCreated) return TRUE;

	AfxEnableControlContainer();

	RECT rectClient;
	GetClientRect(&rectClient);

	// create the control
	if(m_selHtmlCtrl==WEBSTER_CONTROL)
		{
		if (!m_wndWebsterBrowser.Create("untitled",
				WS_CHILD, rectClient, this, AFX_IDW_PANE_FIRST,
				NULL,FALSE,bstrLicKey))
			{ 
			//DestroyWindow();
			return FALSE;
			}
		m_bCtrlCreated=true;
		m_wndWebsterBrowser.SetBorderStyle(0);
		m_wndWebsterBrowser.SetScrollPosVertical(2);
		m_wndWebsterBrowser.SetScrollbarStyleHorizontal(2);
		m_wndWebsterBrowser.SetTitleWindowStyle(0);
		m_wndWebsterBrowser.SetUrlWindowStyle(0);
		m_wndWebsterBrowser.SetBevelStyleInner(0);
		m_wndWebsterBrowser.SetBevelStyleOuter(0);
		m_wndWebsterBrowser.SetBackColor((OLE_COLOR)RGB(255,255,255));
		m_wndWebsterBrowser.SetBrowserName("GRiNS");
		m_wndWebsterBrowser.Navigate("File:///Empty", 
                           NAV_GET | NAV_NAVCREATEFROMTEXT, 
                           0, 
                           "",
                           "<HTML><BODY></BODY></HTML> ",
                           "");
		m_wndWebsterBrowser.ShowWindow(SW_SHOW);	
		}
	else
		{
		if (!m_wndWebBrowser.Create(NULL, "untitled",
				WS_CHILD, rectClient, this, AFX_IDW_PANE_FIRST))
			{
			//DestroyWindow();
			return FALSE;
			}
		m_wndWebBrowser.Navigate("about:",NULL,NULL,NULL,NULL);
		m_wndWebBrowser.ShowWindow(SW_SHOW);
		m_bCtrlCreated=true;
		}
	return TRUE;
	}

void CHtmlWnd::DestroyHtmlCtrl()
	{
	if(!m_bCtrlCreated) return;
	if(m_selHtmlCtrl==WEBSTER_CONTROL)
		m_wndWebsterBrowser.DestroyWindow();
	else
		m_wndWebBrowser.DestroyWindow();
	m_bCtrlCreated=false;
	}


void CHtmlWnd::FitHtmlCtrl()
	{
	if (m_bCtrlCreated)
		{
		CWnd* pwndBrowser=NULL;
		if(m_selHtmlCtrl==WEBSTER_CONTROL)
			pwndBrowser=(CWnd*)&m_wndWebsterBrowser;
		else
			pwndBrowser=(CWnd*)&m_wndWebBrowser;
		// need to push non-client borders out of the client area
		CRect rect;
		GetClientRect(rect);
		::AdjustWindowRectEx(rect,
			pwndBrowser->GetStyle(), FALSE, WS_EX_CLIENTEDGE);
		if(m_isclient)
			pwndBrowser->SetWindowPos(NULL, rect.left, rect.top,
				rect.Width(), rect.Height(), SWP_NOACTIVATE | SWP_NOZORDER);
		else
			pwndBrowser->SetWindowPos(NULL, rect.left+2, rect.top+2,
				rect.Width()-4, rect.Height()-4, SWP_NOACTIVATE | SWP_NOZORDER);
		}
	}

// valid local file URL is
// file:///F|/SMIL/webnews/the.news/html/leader_title.html
void CHtmlWnd::Navigate(LPCTSTR lpszURL)
	{
	if(!m_bCtrlCreated){if(!CreateHtmlCtrl()) return;}

	if(m_selHtmlCtrl==WEBSTER_CONTROL)
		m_wndWebsterBrowser.Navigate(lpszURL,0,0,NULL,NULL,NULL);
	else
		m_wndWebBrowser.Navigate(lpszURL,NULL,NULL,NULL,NULL);
	}

void CHtmlWnd::SetImmHtml(LPCTSTR str)
	{
	if(!m_bCtrlCreated){if(!CreateHtmlCtrl()) return;}
	if(m_selHtmlCtrl==WEBSTER_CONTROL)
		{
		m_wndWebsterBrowser.Navigate("File:///Imm", 
                           NAV_GET | NAV_NAVCREATEFROMTEXT, 
                           0, 
                           "",
                           str,
                           "");
		}
	else
		{
		CString strp("about:");
		m_wndWebBrowser.Navigate(strp+str,NULL,NULL,NULL,NULL);
		}
	}
void CHtmlWnd::Refresh()
	{
	if(!m_bCtrlCreated)return;

	if(m_selHtmlCtrl==WEBSTER_CONTROL)
		m_wndWebsterBrowser.Refresh();
	else
		m_wndWebBrowser.Refresh();
	}
void CHtmlWnd::SetBackColor(COLORREF clr)
	{
	if(!m_bCtrlCreated){if(!CreateHtmlCtrl()) return;}

	if(m_selHtmlCtrl==WEBSTER_CONTROL)
		m_wndWebsterBrowser.SetBackColor(OLE_COLOR(clr));		

	}

/////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////
// the respective Python class
class PYW_EXPORT PyCHtmlWnd : public PyCWnd 
	{
	protected:
	PyCHtmlWnd() {}
	~PyCHtmlWnd(){}
	public:
	static CHtmlWnd *GetHtmlWndPtr(PyObject *self);
	static ui_type_CObject type;
	};


// static mapping helper between c++ obj and python obj
CHtmlWnd* PyCHtmlWnd::GetHtmlWndPtr(PyObject *self)
	{
	return (CHtmlWnd *)PyCWnd::GetPythonGenericWnd(self, &PyCHtmlWnd::type);
	}

//////////////////////////////////////////////////////
// dublet creation function: c++/mfc and Python respective object
// @pymethod <o PyCHtmlWnd>|win32ui|CreateHtmlWnd
PyObject *
py_create_html_wnd(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	CWnd *pHtmlWnd = new CPythonWndFramework<CHtmlWnd>();
	return ui_assoc_object::make( PyCHtmlWnd::type, pHtmlWnd);
	}


//////////////////////////////////////////////////////
// Python object methods implemented by delegating to the coresponding c++/mfc object
// @pymethod |PyCHtmlWnd|CreateWindow|Creates the actual window
static PyObject *
py_create_window(PyObject *self, PyObject *args)
	{
	int style, id;
	PyObject *obParent;
	RECT rect;
	const char *szClass, *szWndName;
	CCreateContext *pCCPass = NULL;
	PythonCreateContext cc;
	PyObject *contextObject = Py_None;
	if (!PyArg_ParseTuple(args, "zzi(iiii)Oi|O:CreateWindow",
	          &szClass,   // @pyparm string|classId||The class ID for the window, or None
	          &szWndName, // @pyparm string|windowName||The title for the window, or None
			   &style, // @pyparm int|style||The style for the window.
			   &rect.left,&rect.top,&rect.right,&rect.bottom,
			   // @pyparm (left, top, right, bottom)|rect||The size and position of the window.
			   &obParent, // @pyparm <o PyCWnd>|parent||The parent window of the new window..
			   &id, // @pyparm int|id||The control's ID. 
			   &contextObject)) // @pyparm object|context||A CreateContext object.
		return NULL;

	CWnd *pParent;
	if (obParent==Py_None)
		pParent = NULL;
	else if (ui_base_class::is_uiobject(obParent, &PyCWnd::type))
		pParent = GetWndPtr( obParent );
	else
		RETURN_TYPE_ERR("parent argument must be a window object, or None");
	CHtmlWnd *pHtmlWnd=PyCHtmlWnd::GetHtmlWndPtr(self);

	if (contextObject != Py_None) 
		{
		cc.SetPythonObject(contextObject);
		pCCPass = &cc;
		}

	if (pParent==NULL)return NULL;
	if (!pHtmlWnd)return NULL;

	GUI_BGN_SAVE;
	BOOL ok = pHtmlWnd->Create(szClass, szWndName, style, rect, pParent, id, pCCPass);
	GUI_END_SAVE;

	if (!ok)RETURN_ERR("PyCHtmlWnd::Create failed");
	RETURN_NONE;
	}

  // @pymethod |PyCHtmlWnd|UseControl|Set which control will be used (IE=0 or WEBSTER=1)
static PyObject *
py_use_html_ctrl(PyObject *self, PyObject *args)
	{
	int selCtrl;
	if(!PyArg_ParseTuple(args, "i", &selCtrl))
		return NULL;

	CHtmlWnd *pHtmlWnd=PyCHtmlWnd::GetHtmlWndPtr(self);
	if(pHtmlWnd==NULL) return NULL;

	GUI_BGN_SAVE;
	pHtmlWnd->UseHtmlCtrl(selCtrl);
	GUI_END_SAVE;

	RETURN_NONE;
	}

// @pymethod |PyCHtmlWnd|Navigate|Navigate to url
static PyObject *
py_navigate(PyObject *self, PyObject *args)
	{
	char* strUrl;
	if(!PyArg_ParseTuple(args, "s", &strUrl))
		return NULL;

	CHtmlWnd *pHtmlWnd=PyCHtmlWnd::GetHtmlWndPtr(self);
	if(pHtmlWnd==NULL) return NULL;

	GUI_BGN_SAVE;
	pHtmlWnd->Navigate(strUrl);
	GUI_END_SAVE;

	RETURN_NONE;
	}
// @pymethod |PyCHtmlWnd|SetImmHtml|Set immediate html
static PyObject *
py_set_imm_html(PyObject *self, PyObject *args)
	{
	char* strHtml;
	if(!PyArg_ParseTuple(args, "s", &strHtml))
		return NULL;

	CHtmlWnd *pHtmlWnd=PyCHtmlWnd::GetHtmlWndPtr(self);
	if(pHtmlWnd==NULL) return NULL;

	GUI_BGN_SAVE;
	pHtmlWnd->SetImmHtml(strHtml);
	GUI_END_SAVE;

	RETURN_NONE;
	}

// @pymethod |PyCHtmlWnd|Refresh|Refresh 
static PyObject *
py_refresh(PyObject *self, PyObject *args)
	{
	CHtmlWnd *pHtmlWnd=PyCHtmlWnd::GetHtmlWndPtr(self);
	if(pHtmlWnd==NULL) return NULL;

	GUI_BGN_SAVE;
	pHtmlWnd->Refresh();
	GUI_END_SAVE;

	RETURN_NONE;
	}


// @pymethod |PyCHtmlWnd|SetClient|Sets a flag used for proper resizing
static PyObject *
py_set_client(PyObject *self, PyObject *args)
	{
	int isclient;
	if(!PyArg_ParseTuple(args, "i", &isclient))
		return NULL;

	CHtmlWnd *pHtmlWnd=PyCHtmlWnd::GetHtmlWndPtr(self);
	if(pHtmlWnd==NULL) return NULL;


	GUI_BGN_SAVE;
	pHtmlWnd->SetClient((isclient!=0));
	GUI_END_SAVE;
	RETURN_NONE;
	}


// @pymethod |PyCHtmlWnd|SetBackColor|Sets the background color
static PyObject *
py_set_back_color(PyObject *self, PyObject *args)
	{
	long color;
	if(!PyArg_ParseTuple(args, "i",&color))
		return NULL;

	CHtmlWnd *pHtmlWnd=PyCHtmlWnd::GetHtmlWndPtr(self);
	if(pHtmlWnd==NULL) return NULL;


	GUI_BGN_SAVE;
	pHtmlWnd->SetBackColor(color);
	GUI_END_SAVE;
	RETURN_NONE;
	}

// @pymethod |PyCHtmlWnd|GetForeignUrl|
static PyObject *
py_get_foreign_url(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	CHtmlWnd *pHtmlWnd=PyCHtmlWnd::GetHtmlWndPtr(self);
	if(pHtmlWnd==NULL) return NULL;
	return Py_BuildValue("s",pHtmlWnd->GetForeignUrl());
	}

// @pymethod |PyCHtmlWnd|CreateHtmlCtrl|
static PyObject *
py_create_html_ctrl(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	CHtmlWnd *pHtmlWnd=PyCHtmlWnd::GetHtmlWndPtr(self);
	if(pHtmlWnd==NULL) return NULL;

	GUI_BGN_SAVE;
	BOOL bRes=pHtmlWnd->CreateHtmlCtrl();
	GUI_END_SAVE;

	if(!bRes) 
		RETURN_ERR("Failed to create Browser control. Check that the browser control you have selected is installed");

	RETURN_NONE;
	}

// @pymethod |PyCHtmlWnd|DestroyHtmlCtrl|
static PyObject *
py_destroy_html_ctrl(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	CHtmlWnd *pHtmlWnd=PyCHtmlWnd::GetHtmlWndPtr(self);
	if(pHtmlWnd==NULL) return NULL;

	GUI_BGN_SAVE;
	pHtmlWnd->DestroyHtmlCtrl();
	GUI_END_SAVE;

	RETURN_NONE;
	}

// @pymethod |PyCHtmlWnd|FitHtmlCtrl|
static PyObject *
py_fit_html_ctrl(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	CHtmlWnd *pHtmlWnd=PyCHtmlWnd::GetHtmlWndPtr(self);
	if(pHtmlWnd==NULL) return NULL;

	GUI_BGN_SAVE;
	pHtmlWnd->FitHtmlCtrl();
	GUI_END_SAVE;

	RETURN_NONE;
	}
static PyObject *
py_has_html_ctrl(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	CHtmlWnd *pHtmlWnd=PyCHtmlWnd::GetHtmlWndPtr(self);
	if(pHtmlWnd==NULL) return NULL;
	GUI_BGN_SAVE;
	int res=pHtmlWnd->HasHtmlCtrl()?1:0;
	GUI_END_SAVE;
	return Py_BuildValue("i",res);
	}

//////////////////////////////////////////////////////
// @object PyCHtmlWnd|
static struct PyMethodDef PyCHtmlWnd_methods[] = {
	{"Navigate",py_navigate,1},
	{"SetImmHtml",py_set_imm_html,1},
	{"Refresh",py_refresh,1},
	{"SetBackColor",py_set_back_color,1},
	{"SetClient",py_set_client,1},
	{"GetForeignUrl",py_get_foreign_url,1},
	{"UseHtmlCtrl",py_use_html_ctrl,1},
	{"CreateHtmlCtrl",py_create_html_ctrl,1},
	{"DestroyHtmlCtrl",py_destroy_html_ctrl,1},
	{"FitHtmlCtrl",py_fit_html_ctrl,1},
	{"HasHtmlCtrl",py_has_html_ctrl,1},
	{NULL,NULL,1}		
};


ui_type_CObject PyCHtmlWnd::type("PyCHtmlWnd", 
								 &PyCWnd::type, 
								 RUNTIME_CLASS(CHtmlWnd), 
								 sizeof(PyCHtmlWnd), 
								 PyCHtmlWnd_methods, 
								 GET_PY_CTOR(PyCHtmlWnd));
