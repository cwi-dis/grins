#include "stdafx.h"

#include "win32win.h"
#include "win32uiExt.h"

#include <afxdisp.h>
#include <exdisp.h>

// Adobe's SVG Viewer control
#include "..\..\..\cmif\win32\SVG\Adobe\svgctl.h"

// hardcoded id of control (for notifications)
#define IDC_SVGCTL 9000

// the c++/mfc class 
class CSvgWnd: public CWnd
	{
	protected:
	DECLARE_DYNCREATE(CSvgWnd)

	public:
	CSvgWnd();
	virtual ~CSvgWnd();
	virtual BOOL Create(LPCTSTR lpszClassName, LPCTSTR lpszWindowName,
		DWORD dwStyle, const RECT& rect, CWnd* pParentWnd, UINT nID,
		CCreateContext* pContext = NULL);

	// Control creation
	BOOL CreateSvgCtrl();
	void DestroySvgCtrl();
	bool HasSvgCtrl(){return m_bCtrlCreated;}

	// Operations
	public:
	void SetSrc(LPCTSTR lpszURL);
	void Reload();

	// Dim helpers
	void SetClient(bool b){m_isclient=b;}
	void FitSvgCtrl();

	private:
	CSVGCtl m_wndSvgCtrl;
	bool m_isclient;
	bool m_bCtrlCreated;

	BSTR bstrLicKey;

	// Generated message map functions
	protected:
	//{{AFX_MSG(CSvgWnd)
	afx_msg void OnSize(UINT nType, int cx, int cy);
	afx_msg void OnPaint();
	afx_msg void OnDestroy();
	DECLARE_EVENTSINK_MAP()
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
	};

///////////////////////////////////////////////
//   IMPLEMENTATION

IMPLEMENT_DYNCREATE(CSvgWnd, CWnd)

BEGIN_MESSAGE_MAP(CSvgWnd, CWnd)
	//{{AFX_MSG_MAP(CSVGView)
	ON_WM_SIZE()
	ON_WM_PAINT()
	ON_WM_DESTROY()
	//}}AFX_MSG_MAP
END_MESSAGE_MAP()


BEGIN_EVENTSINK_MAP(CSvgWnd, CWnd)
    //{{AFX_EVENTSINK_MAP(CContainerWnd)
	//ON_EVENT(CSvgWnd, IDC_SVGCTL, 201 /* onclick */, OnClickSvg, VTS_BSTR)
	//ON_EVENT(CSvgWnd, IDC_SVGCTL, 202 /* onmouseover */, OnMouseOverSvg, VTS_BSTR)
	//ON_EVENT(CSvgWnd, IDC_SVGCTL, 203 /* onmouseout */, OnMouseOutSvg, VTS_BSTR)
	//ON_EVENT(CSvgWnd, IDC_SVGCTL, 204 /* onmousemove */, OnMouseMoveSvg, VTS_BSTR)
	//ON_EVENT(CSvgWnd, IDC_SVGCTL, 205 /* onmousedown */, OnMouseDownSvg, VTS_BSTR)
	//ON_EVENT(CSvgWnd, IDC_SVGCTL, 206 /* onmouseup */, OnMouseUpSvg, VTS_BSTR)
	//ON_EVENT(CSvgWnd, IDC_SVGCTL, 207 /* ondblclick */, OnDblClickSvg, VTS_BSTR)
	//ON_EVENT(CSvgWnd, IDC_SVGCTL, 208 /* onkeydown */, OnKeyDownSvg, VTS_BSTR VTS_I4)
	//ON_EVENT(CSvgWnd, IDC_SVGCTL, 209 /* onkeyup */, OnKeyUpSvg, VTS_BSTR VTS_I4)
	//ON_EVENT(CSvgWnd, IDC_SVGCTL, 210 /* onkeypress */, OnKeyPressSvg, VTS_BSTR VTS_I4)
	//ON_EVENT(CSvgWnd, IDC_SVGCTL, 211 /* onzoom */, OnZoomSvg, VTS_NONE)
	//ON_EVENT(CSvgWnd, IDC_SVGCTL, 212 /* onload */, OnLoadSvg, VTS_NONE)
	//ON_EVENT(CSvgWnd, IDC_SVGCTL, 213 /* onunload */, OnUnloadSvg, VTS_NONE)
	//}}AFX_EVENTSINK_MAP
END_EVENTSINK_MAP()

CSvgWnd::CSvgWnd()
:	m_bCtrlCreated(false),
	m_isclient(false)
	{
	}

CSvgWnd::~CSvgWnd()
	{
	}

void CSvgWnd::OnDestroy()
	{
	m_bCtrlCreated=false;
	}

void CSvgWnd::OnSize(UINT nType, int cx, int cy)
	{
	CWnd::OnSize(nType, cx, cy);
	FitSvgCtrl();
	}

void CSvgWnd::OnPaint()
	{
	Default();
	}


/////////////////////////////////////////////////////////////////////////////
// CSvgWnd operations

BOOL CSvgWnd::Create(LPCTSTR lpszClassName, LPCTSTR lpszWindowName,
						DWORD dwStyle, const RECT& rect, CWnd* pParentWnd,
						UINT nID, CCreateContext* pContext)
	{
	if (!CWnd::Create(lpszClassName, lpszWindowName,
		dwStyle, rect, pParentWnd,  nID, pContext))
		return FALSE;
	return TRUE;
	}

BOOL CSvgWnd::CreateSvgCtrl()
	{
	if(m_bCtrlCreated) return TRUE;

	AfxEnableControlContainer();

	RECT rectClient;
	GetClientRect(&rectClient);

	// create the control
	if (!m_wndSvgCtrl.Create(NULL, "untitled", WS_CHILD, rectClient, this, IDC_SVGCTL, NULL))
		{
		//DestroyWindow();
		return FALSE;
		}
	m_bCtrlCreated=true;
	m_wndSvgCtrl.ShowWindow(SW_SHOW);
	return TRUE;
	}

void CSvgWnd::DestroySvgCtrl()
	{
	if(!m_bCtrlCreated) return;
	m_wndSvgCtrl.DestroyWindow();
	m_bCtrlCreated = false;
	}


void CSvgWnd::FitSvgCtrl()
	{
	if (m_bCtrlCreated)
		{
		CWnd* pwnd = &m_wndSvgCtrl;
		// need to push non-client borders out of the client area
		CRect rect;
		GetClientRect(rect);
		::AdjustWindowRectEx(rect,
			pwnd->GetStyle(), FALSE, WS_EX_CLIENTEDGE);
		if(m_isclient)
			pwnd->SetWindowPos(NULL, rect.left, rect.top,
				rect.Width(), rect.Height(), SWP_NOACTIVATE | SWP_NOZORDER);
		else
			pwnd->SetWindowPos(NULL, rect.left+2, rect.top+2,
				rect.Width()-4, rect.Height()-4, SWP_NOACTIVATE | SWP_NOZORDER);
		}
	}

void CSvgWnd::SetSrc(LPCTSTR lpszURL)
	{
	if(!m_bCtrlCreated){if(!CreateSvgCtrl()) return;}
	m_wndSvgCtrl.SetSrc(lpszURL);
	}

void CSvgWnd::Reload()
	{
	if(!m_bCtrlCreated)return;
	m_wndSvgCtrl.reload();
	}
/////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////
// the respective Python class
class PYW_EXPORT PyCSvgWnd : public PyCWnd 
	{
	protected:
	PyCSvgWnd() {}
	~PyCSvgWnd(){}
	public:
	static CSvgWnd *GetSVGWndPtr(PyObject *self);
	static ui_type_CObject type;
	};

//////////////////////////////////////////////////////
// dublet creation function: c++/mfc and Python respective object
// @pymethod <o PyCSvgWnd>|win32ui|CreateSvgWnd
PyObject *
py_create_svg_wnd(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	CWnd *pSVGWnd = new CPythonWndFramework<CSvgWnd>();
	return ui_assoc_object::make( PyCSvgWnd::type, pSVGWnd);
	}

CSvgWnd* PyCSvgWnd::GetSVGWndPtr(PyObject *self)
	{
	return (CSvgWnd *)PyCWnd::GetPythonGenericWnd(self, &PyCSvgWnd::type);
	}

// Detect SVG support

CLSID const& GetClsid()
	{
	static CLSID const clsid
			= { 0x6de3f233, 0xdbe6, 0x11d2, { 0xae, 0x81, 0x0, 0xc0, 0x4f, 0x7f, 0xe3, 0xef } };
	return clsid;
	}

IID const& GetIid()
	{
	static IID const iid
			= { 0xfd1b1a70, 0x10e5, 0x11d4, { 0x90, 0x4b, 0x0, 0xc0, 0x4f, 0x78, 0xac, 0xf9}};
	return iid;
	}

// @pymethod <o PyCSvgWnd>|win32ui|HasSvgSupport
PyObject *
py_has_svg_support(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	IUnknown *pCtrl;
	HRESULT hr = CoCreateInstance(GetClsid(), NULL, CLSCTX_INPROC_SERVER, IID_IUnknown, (void**)&pCtrl);
	int res = 0;
	if(SUCCEEDED(hr))
		{
		res = 1;
		pCtrl->Release();
		}
	return Py_BuildValue("i",res);
	}

//////////////////////////////////////////////////////
// Python object methods implemented by delegating to the coresponding c++/mfc object
// @pymethod |PyCSvgWnd|CreateWindow|Creates the actual window
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
	CSvgWnd *pSVGWnd=PyCSvgWnd::GetSVGWndPtr(self);

	if (contextObject != Py_None) 
		{
		cc.SetPythonObject(contextObject);
		pCCPass = &cc;
		}

	if (pParent==NULL)return NULL;
	if (!pSVGWnd)return NULL;

	GUI_BGN_SAVE;
	BOOL ok = pSVGWnd->Create(szClass, szWndName, style, rect, pParent, id, pCCPass);
	GUI_END_SAVE;

	if (!ok)RETURN_ERR("PyCSvgWnd::Create failed");
	RETURN_NONE;
	}


// @pymethod |PyCSvgWnd|SetSrc|SetSrc to url
static PyObject *
py_set_src(PyObject *self, PyObject *args)
	{
	char* strUrl;
	if(!PyArg_ParseTuple(args, "s", &strUrl))
		return NULL;

	CSvgWnd *pSVGWnd=PyCSvgWnd::GetSVGWndPtr(self);
	if(pSVGWnd==NULL) return NULL;

	GUI_BGN_SAVE;
	pSVGWnd->SetSrc(strUrl);
	GUI_END_SAVE;

	RETURN_NONE;
	}

// @pymethod |PyCSvgWnd|Reload|Reload 
static PyObject *
py_reload(PyObject *self, PyObject *args)
	{
	CSvgWnd *pSVGWnd=PyCSvgWnd::GetSVGWndPtr(self);
	if(pSVGWnd==NULL) return NULL;

	GUI_BGN_SAVE;
	pSVGWnd->Reload();
	GUI_END_SAVE;

	RETURN_NONE;
	}


// @pymethod |PyCSvgWnd|SetClient|Sets a flag used for proper resizing
static PyObject *
py_set_client(PyObject *self, PyObject *args)
	{
	int isclient;
	if(!PyArg_ParseTuple(args, "i", &isclient))
		return NULL;

	CSvgWnd *pSVGWnd=PyCSvgWnd::GetSVGWndPtr(self);
	if(pSVGWnd==NULL) return NULL;


	GUI_BGN_SAVE;
	pSVGWnd->SetClient((isclient!=0));
	GUI_END_SAVE;
	RETURN_NONE;
	}

// @pymethod |PyCSvgWnd|CreateSvgCtrl|
static PyObject *
py_create_svg_ctrl(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	CSvgWnd *pSVGWnd=PyCSvgWnd::GetSVGWndPtr(self);
	if(pSVGWnd==NULL) return NULL;

	GUI_BGN_SAVE;
	BOOL bRes=pSVGWnd->CreateSvgCtrl();
	GUI_END_SAVE;

	if(!bRes) 
		RETURN_ERR("Failed to create Browser control. Check that the browser control you have selected is installed");

	RETURN_NONE;
	}

// @pymethod |PyCSvgWnd|DestroySvgCtrl|
static PyObject *
py_destroy_svg_ctrl(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	CSvgWnd *pSVGWnd=PyCSvgWnd::GetSVGWndPtr(self);
	if(pSVGWnd==NULL) return NULL;

	GUI_BGN_SAVE;
	pSVGWnd->DestroySvgCtrl();
	GUI_END_SAVE;

	RETURN_NONE;
	}

// @pymethod |PyCSvgWnd|FitSvgCtrl|
static PyObject *
py_fit_svg_ctrl(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	CSvgWnd *pSVGWnd=PyCSvgWnd::GetSVGWndPtr(self);
	if(pSVGWnd==NULL) return NULL;

	GUI_BGN_SAVE;
	pSVGWnd->FitSvgCtrl();
	GUI_END_SAVE;

	RETURN_NONE;
	}

static PyObject *
py_has_svg_ctrl(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	CSvgWnd *pSVGWnd=PyCSvgWnd::GetSVGWndPtr(self);
	if(pSVGWnd==NULL) return NULL;
	GUI_BGN_SAVE;
	int res=pSVGWnd->HasSvgCtrl()?1:0;
	GUI_END_SAVE;
	return Py_BuildValue("i",res);
	}

//////////////////////////////////////////////////////
// @object PyCSvgWnd|
static struct PyMethodDef PyCSvgWnd_methods[] = {
	{"SetSrc",py_set_src,1},
	{"Reload",py_reload,1},
	{"SetClient",py_set_client,1},
	{"CreateSvgCtrl",py_create_svg_ctrl,1},
	{"DestroySvgCtrl",py_destroy_svg_ctrl,1},
	{"FitSvgCtrl",py_fit_svg_ctrl,1},
	{"HasSvgCtrl",py_has_svg_ctrl,1},
	{NULL,NULL,1}		
};


ui_type_CObject PyCSvgWnd::type("PyCSvgWnd", 
								 &PyCWnd::type, 
								 RUNTIME_CLASS(CSvgWnd), 
								 sizeof(PyCSvgWnd), 
								 PyCSvgWnd_methods, 
								 GET_PY_CTOR(PyCSvgWnd));
