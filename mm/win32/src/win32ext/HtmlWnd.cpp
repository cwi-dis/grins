// CMIF_ADD
//
// kk@epsilon.com.gr
//

#include "stdafx.h"

#include "win32win.h"
#include "win32uiExt.h"

#include <afxdisp.h>
#include <exdisp.h>

#define RELEASE(lpUnk) do \
	{ if ((lpUnk) != NULL) { (lpUnk)->Release(); (lpUnk) = NULL; } } while (0)

// the c++/mfc class 
class CHtmlWnd: public CWnd
	{
	protected:
	DECLARE_DYNCREATE(CHtmlWnd)
	DECLARE_EVENTSINK_MAP()

	// Overrides
	public:
	virtual BOOL Create(LPCTSTR lpszClassName, LPCTSTR lpszWindowName,
		DWORD dwStyle, const RECT& rect, CWnd* pParentWnd, UINT nID,
		CCreateContext* pContext = NULL);
	BOOL CreateHtmlCtrl();
	void DestroyHtmlCtrl();
	void FitHtmlCtrl();

	public:
	// Events
	virtual void OnBeforeNavigate2(LPCTSTR lpszURL, DWORD nFlags,
		LPCTSTR lpszTargetFrameName, CByteArray& baPostedData,
		LPCTSTR lpszHeaders, BOOL* pbCancel);
	
	// Event reflectors (not normally overridden)
	protected:
	virtual void BeforeNavigate2(LPDISPATCH pDisp, VARIANT* URL,
		VARIANT* Flags, VARIANT* TargetFrameName, VARIANT* PostData,
		VARIANT* Headers,   BOOL* Cancel);


	// Operations
	public:
	void GoBack();
	void GoForward();
	void GoHome();
	void GoSearch();
	void Navigate(LPCTSTR URL, DWORD dwFlags = 0,
		LPCTSTR lpszTargetFrameName = NULL,
		LPCTSTR lpszHeaders = NULL, LPVOID lpvPostData = NULL,
		DWORD dwPostDataLen = 0);

	public:
	CHtmlWnd():m_pBrowser(NULL),m_isclient(false){}
	virtual ~CHtmlWnd(){RELEASE(m_pBrowser);}
	CWnd m_wndBrowser;
	IWebBrowser* m_pBrowser;
	bool m_isclient;

	// custom support
	CString m_foreignUrl;
	LPCTSTR GetForeignUrl(){return m_foreignUrl;}
	void SetClient(bool b){m_isclient=b;}

	// Generated message map functions
	protected:
	//{{AFX_MSG(CHtmlWnd)
	afx_msg void OnSize(UINT nType, int cx, int cy);
	afx_msg void OnPaint();
	afx_msg void OnDestroy();
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()


	};

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
	ON_EVENT(CHtmlWnd, AFX_IDW_PANE_FIRST, 250 /* BeforeNavigate2 */, BeforeNavigate2, VTS_DISPATCH VTS_PVARIANT VTS_PVARIANT VTS_PVARIANT VTS_PVARIANT VTS_PVARIANT VTS_PBOOL)
	//}}AFX_EVENTSINK_MAP
END_EVENTSINK_MAP()

void CHtmlWnd::OnDestroy()
	{
	RELEASE(m_pBrowser);
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


void CHtmlWnd::BeforeNavigate2(LPDISPATCH /* pDisp */, VARIANT* URL,
		VARIANT* Flags, VARIANT* TargetFrameName,
		VARIANT* PostData, VARIANT* Headers, BOOL* Cancel)
	{
	ASSERT(V_VT(URL) == VT_BSTR);
	ASSERT(V_VT(TargetFrameName) == VT_BSTR);
	ASSERT(V_VT(PostData) == (VT_VARIANT | VT_BYREF));
	ASSERT(V_VT(Headers) == VT_BSTR);
	ASSERT(Cancel != NULL);

	USES_CONVERSION;

	VARIANT* vtPostedData = V_VARIANTREF(PostData);
	CByteArray array;
	if (V_VT(vtPostedData) & VT_ARRAY)
		{
		// must be a vector of bytes
		ASSERT(vtPostedData->parray->cDims == 1 && vtPostedData->parray->cbElements == 1);

		vtPostedData->vt |= VT_UI1;
		COleSafeArray safe(vtPostedData);

		DWORD dwSize = safe.GetOneDimSize();
		LPVOID pVoid;
		safe.AccessData(&pVoid);

		array.SetSize(dwSize);
		LPBYTE lpByte = array.GetData();

		memcpy(lpByte, pVoid, dwSize);
		safe.UnaccessData();
		}
	// make real parameters out of the notification

	CString strTargetFrameName(V_BSTR(TargetFrameName));
	CString strURL = V_BSTR(URL);
	CString strHeaders = V_BSTR(Headers);
	DWORD nFlags = V_I4(Flags);

	// notify the user's class
	OnBeforeNavigate2(strURL, nFlags, strTargetFrameName,
		array, strHeaders, Cancel);
	}

void CHtmlWnd::OnBeforeNavigate2(LPCTSTR lpszURL, DWORD nFlags,
	LPCTSTR lpszTargetFrameName, CByteArray& baPostData,
	LPCTSTR lpszHeaders, BOOL* bCancel)
	{
	// default to continuing
	*bCancel = FALSE;

	// check for foreign format
	CString url(lpszURL);
	CString prefix= "cmif:";
	if (url.Find(prefix)!=-1)
		{
		m_foreignUrl=url;
		PostMessage(WM_USER); // notify user to get it
		*bCancel=TRUE;
		return;
		}	
	UNUSED_ALWAYS(nFlags);
	UNUSED_ALWAYS(lpszTargetFrameName);
	UNUSED_ALWAYS(baPostData);
	UNUSED_ALWAYS(lpszHeaders);
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
	if(m_pBrowser) return TRUE;

	AfxEnableControlContainer();

	RECT rectClient;
	GetClientRect(&rectClient);

	// create the control window
	// AFX_IDW_PANE_FIRST is a safe but arbitrary ID
	if (!m_wndBrowser.CreateControl(CLSID_WebBrowser, "untitled",
				WS_VISIBLE | WS_CHILD, rectClient, this, AFX_IDW_PANE_FIRST))
		{
		DestroyWindow();
		return FALSE;
		}

	LPUNKNOWN lpUnk = m_wndBrowser.GetControlUnknown();
	HRESULT hr = lpUnk->QueryInterface(IID_IWebBrowser2, (void**) &m_pBrowser);
	if (!SUCCEEDED(hr))
		{
		m_pBrowser = NULL;
		m_wndBrowser.DestroyWindow();
		DestroyWindow();
		return FALSE;
		}

	return TRUE;
	}

void CHtmlWnd::DestroyHtmlCtrl()
	{
	if(m_pBrowser)
		{
		m_pBrowser->Release();
		m_pBrowser=NULL;
		m_wndBrowser.DestroyWindow();
		}
	}


void CHtmlWnd::FitHtmlCtrl()
	{
	if (::IsWindow(m_wndBrowser.m_hWnd))
		{
		// need to push non-client borders out of the client area
		CRect rect;
		GetClientRect(rect);
		::AdjustWindowRectEx(rect,
			m_wndBrowser.GetStyle(), FALSE, WS_EX_CLIENTEDGE);
		if(m_isclient)
			m_wndBrowser.SetWindowPos(NULL, rect.left, rect.top,
				rect.Width(), rect.Height(), SWP_NOACTIVATE | SWP_NOZORDER);
		else
			m_wndBrowser.SetWindowPos(NULL, rect.left+2, rect.top+2,
				rect.Width()-4, rect.Height()-4, SWP_NOACTIVATE | SWP_NOZORDER);
		}
	}

void CHtmlWnd::Navigate(LPCTSTR lpszURL, DWORD dwFlags /* = 0 */,
	LPCTSTR lpszTargetFrameName /* = NULL */ ,
	LPCTSTR lpszHeaders /* = NULL */, LPVOID lpvPostData /* = NULL */,
	DWORD dwPostDataLen /* = 0 */)
	{
	if(!m_pBrowser) return;

	CString strURL(lpszURL);
	BSTR bstrURL = strURL.AllocSysString();

	COleSafeArray vPostData;
	if (lpvPostData != NULL)
		{
		if (dwPostDataLen == 0)
			dwPostDataLen = lstrlen((LPCTSTR) lpvPostData);

		vPostData.CreateOneDim(VT_UI1, dwPostDataLen, lpvPostData);
		}

	m_pBrowser->Navigate(bstrURL,
		COleVariant((long) dwFlags, VT_I4),
		COleVariant(lpszTargetFrameName, VT_BSTR),
		vPostData,
		COleVariant(lpszHeaders, VT_BSTR));
	}

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
	if(pHtmlWnd->m_pBrowser==NULL)
		pHtmlWnd->CreateHtmlCtrl();
	pHtmlWnd->Navigate(strUrl,NULL,NULL,NULL,NULL);
	GUI_END_SAVE;

	if(pHtmlWnd->m_pBrowser==NULL) 
			RETURN_ERR("Failed to create Browser control. Check that IE4 is installed");
	

	RETURN_NONE;
	}
// @pymethod |PyCHtmlWnd|Refresh|Refresh 
static PyObject *
py_refresh(PyObject *self, PyObject *args)
	{
	CHtmlWnd *pHtmlWnd=PyCHtmlWnd::GetHtmlWndPtr(self);
	if(pHtmlWnd==NULL) return NULL;


	GUI_BGN_SAVE;
	if(pHtmlWnd->m_pBrowser!=NULL)
		pHtmlWnd->m_pBrowser->Refresh();
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
	pHtmlWnd->CreateHtmlCtrl();
	GUI_END_SAVE;

	if(pHtmlWnd->m_pBrowser==NULL) 
			RETURN_ERR("Failed to create Browser control. Check that IE4 is installed");

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

//	{"CreateWindow",py_create_window,1}, // @pymeth CreateWindow|Create the underlying window object

//////////////////////////////////////////////////////
// @object PyCHtmlWnd|
static struct PyMethodDef PyCHtmlWnd_methods[] = {
	{"Navigate",py_navigate,1},
	{"Refresh",py_refresh,1},
	{"SetClient",py_set_client,1},
	{"GetForeignUrl",py_get_foreign_url,1},
	{"CreateHtmlCtrl",py_create_html_ctrl,1},
	{"DestroyHtmlCtrl",py_destroy_html_ctrl,1},
	{"FitHtmlCtrl",py_fit_html_ctrl,1},
	{NULL,NULL,1}		
};


ui_type_CObject PyCHtmlWnd::type("PyCHtmlWnd", 
								 &PyCWnd::type, 
								 RUNTIME_CLASS(CHtmlWnd), 
								 sizeof(PyCHtmlWnd), 
								 PyCHtmlWnd_methods, 
								 GET_PY_CTOR(PyCHtmlWnd));
