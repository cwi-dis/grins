#include "stdafx.h"

#include "realaudio.h"

// the c++/mfc class
class CRPlayer: public CWnd
	{
	protected:
	DECLARE_DYNCREATE(CRPlayer)
	DECLARE_EVENTSINK_MAP()
	DECLARE_MESSAGE_MAP()

	public:
	CRPlayer():m_bCtrlCreated(false),m_isclient(false){}
	virtual ~CRPlayer(){}
	virtual BOOL Create(LPCTSTR lpszClassName, LPCTSTR lpszWindowName,
		DWORD dwStyle, const RECT& rect, CWnd* pParentWnd, UINT nID,
		CCreateContext* pContext = NULL);

	// Control creation
	BOOL CreateRPlayerCtrl();
	void DestroyRPlayerCtrl();

	// Operations
	public:

	/////////////////
	// Control's methods (not complete)
	void SetSource(LPCTSTR lpszURL);
	void SetControls(LPCTSTR lpszNewValue);

	void DoPlay();
	void DoStop();
	void DoPause();
	void DoPlayPause();

	BOOL CanPlay();
	BOOL CanPause();
	BOOL CanStop();

	long GetPosition();
	long GetPlayState();
	long GetLength();
	/////////////////

	void SetClient(bool b){m_isclient=b;}
	void FitRPlayerCtrl();

	private:
	CRealAudio m_rpCtrl;
	bool m_isclient;
	bool m_bCtrlCreated;

	// Generated message map functions
	protected:
	//{{AFX_MSG(CRPlayer)
	afx_msg void OnSize(UINT nType, int cx, int cy);
	afx_msg void OnPaint();
	//}}AFX_MSG
	};

IMPLEMENT_DYNCREATE(CRPlayer, CWnd)

BEGIN_MESSAGE_MAP(CRPlayer, CWnd)
	//{{AFX_MSG_MAP(CHtmlView)
	ON_WM_SIZE()
	ON_WM_PAINT()
	//}}AFX_MSG_MAP
END_MESSAGE_MAP()

BEGIN_EVENTSINK_MAP(CRPlayer, CWnd)
    //{{AFX_EVENTSINK_MAP(CContainerWnd)
	//}}AFX_EVENTSINK_MAP
END_EVENTSINK_MAP()

#define ASSERT_CTRL_EXISTS if(!m_bCtrlCreated){if(!CreateRPlayerCtrl()) return;}
#define ASSERT_CTRL_EXISTS_T if(!m_bCtrlCreated){if(!CreateRPlayerCtrl()) return TRUE;}
#define ASSERT_CTRL_EXISTS_F if(!m_bCtrlCreated){if(!CreateRPlayerCtrl()) return FALSE;}

void CRPlayer::OnSize(UINT nType, int cx, int cy)
	{
	CWnd::OnSize(nType, cx, cy);
	FitRPlayerCtrl();
	}

void CRPlayer::OnPaint()
	{
	Default();
	}

BOOL CRPlayer::Create(LPCTSTR lpszClassName, LPCTSTR lpszWindowName,
						DWORD dwStyle, const RECT& rect, CWnd* pParentWnd,
						UINT nID, CCreateContext* pContext)
	{
	if (!CWnd::Create(lpszClassName, lpszWindowName,
		dwStyle, rect, pParentWnd,  nID, pContext))
		return FALSE;
	return TRUE;
	}

BOOL CRPlayer::CreateRPlayerCtrl()
	{
	if(m_bCtrlCreated) return TRUE;

	AfxEnableControlContainer();

	RECT rectClient;
	GetClientRect(&rectClient);

	// create the control
	if (!m_rpCtrl.Create(NULL, "untitled",
			WS_CHILD|WS_VISIBLE, rectClient, this, AFX_IDW_PANE_FIRST))
		{
		DestroyWindow();
		return FALSE;
		}
	m_rpCtrl.SetNoLabels(TRUE);
	m_rpCtrl.ShowWindow(SW_SHOW);
	m_bCtrlCreated=true;
	return TRUE;
	}

void CRPlayer::DestroyRPlayerCtrl()
	{
	if(!m_bCtrlCreated) return;
	m_rpCtrl.DestroyWindow();
	}

void CRPlayer::FitRPlayerCtrl()
	{
	if (!m_bCtrlCreated) return;
	CRect rect;
	GetClientRect(rect);
	::AdjustWindowRectEx(rect,
		m_rpCtrl.GetStyle(), FALSE, WS_EX_CLIENTEDGE);
	if(m_isclient)
		m_rpCtrl.SetWindowPos(NULL, rect.left, rect.top,
			rect.Width(), rect.Height(), SWP_NOACTIVATE | SWP_NOZORDER);
	else
		m_rpCtrl.SetWindowPos(NULL, rect.left+2, rect.top+2,
			rect.Width()-4, rect.Height()-4, SWP_NOACTIVATE | SWP_NOZORDER);
	}

// Control methods (not complete)
void CRPlayer::SetSource(LPCTSTR lpszURL){ASSERT_CTRL_EXISTS;m_rpCtrl.SetSource(lpszURL);}
void CRPlayer::SetControls(LPCTSTR lpszNewValue){ASSERT_CTRL_EXISTS;m_rpCtrl.SetControls(lpszNewValue);}

void CRPlayer::DoPlay(){ASSERT_CTRL_EXISTS;m_rpCtrl.DoPlay();}
void CRPlayer::DoStop(){ASSERT_CTRL_EXISTS;m_rpCtrl.DoStop();}
void CRPlayer::DoPause(){ASSERT_CTRL_EXISTS;m_rpCtrl.DoPause();}
void CRPlayer::DoPlayPause(){ASSERT_CTRL_EXISTS;m_rpCtrl.DoPlayPause();}

BOOL CRPlayer::CanPlay(){ASSERT_CTRL_EXISTS_F;return m_rpCtrl.CanPlay();}
BOOL CRPlayer::CanPause(){ASSERT_CTRL_EXISTS_T;return m_rpCtrl.CanPause();}
BOOL CRPlayer::CanStop(){ASSERT_CTRL_EXISTS_T;return m_rpCtrl.CanStop();}

long CRPlayer::GetPosition(){ASSERT_CTRL_EXISTS_F;return m_rpCtrl.GetPosition();}
long CRPlayer::GetPlayState(){ASSERT_CTRL_EXISTS_F;return m_rpCtrl.GetPlayState();}
long CRPlayer::GetLength(){ASSERT_CTRL_EXISTS_F;return m_rpCtrl.GetLength();}

/////////////////////////////////////////////////////////


// the respective Python class
class PYW_EXPORT PyCRPlayer : public PyCWnd 
	{
	protected:
	PyCRPlayer() {}
	~PyCRPlayer(){}
	public:
	static CRPlayer *GetRPlayerWndPtr(PyObject *self);
	static ui_type_CObject type;
	};


// static mapping helper between c++ obj and python obj
CRPlayer* PyCRPlayer::GetRPlayerWndPtr(PyObject *self)
	{
	return (CRPlayer *)PyCWnd::GetPythonGenericWnd(self, &PyCRPlayer::type);
	}

//////////////////////////////////////////////////////
// dublet creation function: c++/mfc and Python respective object
// @pymethod <o PyCRPlayer>|win32ui|CreateRPlayer
PyObject *
py_create_rplayer(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	CWnd *pRPlayer = new CPythonWndFramework<CRPlayer>();
	return ui_assoc_object::make( PyCRPlayer::type, pRPlayer);
	}

//////////////////////////////////////////////////////
// Python object methods implemented by delegating to the coresponding c++/mfc object
// @pymethod |PyCRPlayer|CreateWindow|Creates the actual window
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
	CRPlayer *pRPlayer=PyCRPlayer::GetRPlayerWndPtr(self);

	if (contextObject != Py_None) 
		{
		cc.SetPythonObject(contextObject);
		pCCPass = &cc;
		}

	if (pParent==NULL)return NULL;
	if (!pRPlayerWnd)return NULL;

	GUI_BGN_SAVE;
	BOOL ok = pRPlayer->Create(szClass, szWndName, style, rect, pParent, id, pCCPass);
	GUI_END_SAVE;

	if (!ok)RETURN_ERR("PyCRPlayer::Create failed");
	RETURN_NONE;
	}


// @pymethod |PyCRPlayer|SetSource|SetSource to url
static PyObject *
py_set_source(PyObject *self, PyObject *args)
	{
	char* strUrl;
	if(!PyArg_ParseTuple(args, "s", &strUrl))
		return NULL;

	CRPlayer *pRPlayer=PyCRPlayer::GetRPlayerWndPtr(self);
	if(pRPlayer==NULL) return NULL;

	GUI_BGN_SAVE;
	pRPlayer->SetSource(strUrl);
	GUI_END_SAVE;

	RETURN_NONE;
	}
// @pymethod |PyCRPlayer|SetControls|SetControls
static PyObject *
py_set_controls(PyObject *self, PyObject *args)
	{
	char* strSp;
	if(!PyArg_ParseTuple(args, "s", &strSp))
		return NULL;

	CRPlayer *pRPlayer=PyCRPlayer::GetRPlayerWndPtr(self);
	if(pRPlayer==NULL) return NULL;

	GUI_BGN_SAVE;
	pRPlayer->SetControls(strSp);
	GUI_END_SAVE;

	RETURN_NONE;
	}

// @pymethod |PyCRPlayer|DoPlay|DoPlay 
static PyObject *
py_do_play(PyObject *self, PyObject *args)
	{
	CRPlayer *pRPlayer=PyCRPlayer::GetRPlayerWndPtr(self);
	if(pRPlayer==NULL) return NULL;
	GUI_BGN_SAVE;
	pRPlayer->DoPlay();
	GUI_END_SAVE;
	RETURN_NONE;
	}
// @pymethod |PyCRPlayer|DoStop|DoStop 
static PyObject *
py_do_stop(PyObject *self, PyObject *args)
	{
	CRPlayer *pRPlayer=PyCRPlayer::GetRPlayerWndPtr(self);
	if(pRPlayer==NULL) return NULL;
	GUI_BGN_SAVE;
	pRPlayer->DoStop();
	GUI_END_SAVE;
	RETURN_NONE;
	}
// @pymethod |PyCRPlayer|DoPause|DoPause 
static PyObject *
py_do_pause(PyObject *self, PyObject *args)
	{
	CRPlayer *pRPlayer=PyCRPlayer::GetRPlayerWndPtr(self);
	if(pRPlayer==NULL) return NULL;
	GUI_BGN_SAVE;
	pRPlayer->DoPause();
	GUI_END_SAVE;
	RETURN_NONE;
	}
// @pymethod |PyCRPlayer|DoPlayPause|DoPlayPause 
static PyObject *
py_do_play_pause(PyObject *self, PyObject *args)
	{
	CRPlayer *pRPlayer=PyCRPlayer::GetRPlayerWndPtr(self);
	if(pRPlayer==NULL) return NULL;
	GUI_BGN_SAVE;
	pRPlayer->DoPlayPause();
	GUI_END_SAVE;
	RETURN_NONE;
	}


// @pymethod |PyCRPlayer|CanPlay|CanPlay 
static PyObject *
py_can_play(PyObject *self, PyObject *args)
	{
	CRPlayer *pRPlayer=PyCRPlayer::GetRPlayerWndPtr(self);
	if(pRPlayer==NULL) return NULL;
	GUI_BGN_SAVE;
	BOOL bRet=pRPlayer->CanPlay();
	GUI_END_SAVE;
	return Py_BuildValue("i",bRet);	
	}
// @pymethod |PyCRPlayer|CanStop|CanStop
static PyObject *
py_can_stop(PyObject *self, PyObject *args)
	{
	CRPlayer *pRPlayer=PyCRPlayer::GetRPlayerWndPtr(self);
	if(pRPlayer==NULL) return NULL;
	GUI_BGN_SAVE;
	BOOL bRet=pRPlayer->CanStop();
	GUI_END_SAVE;
	return Py_BuildValue("i",bRet);	
	}
// @pymethod |PyCRPlayer|CanPause|CanPause
static PyObject *
py_can_pause(PyObject *self, PyObject *args)
	{
	CRPlayer *pRPlayer=PyCRPlayer::GetRPlayerWndPtr(self);
	if(pRPlayer==NULL) return NULL;
	GUI_BGN_SAVE;
	BOOL bRet=pRPlayer->CanPause();
	GUI_END_SAVE;
	return Py_BuildValue("i",bRet);	
	}

// @pymethod |PyCRPlayer|GetPosition|GetPosition
static PyObject *
py_get_position(PyObject *self, PyObject *args)
	{
	CRPlayer *pRPlayer=PyCRPlayer::GetRPlayerWndPtr(self);
	if(pRPlayer==NULL) return NULL;
	GUI_BGN_SAVE;
	long lRet=pRPlayer->GetPosition();
	GUI_END_SAVE;
	return Py_BuildValue("l",lRet);	
	}
// @pymethod |PyCRPlayer|GetPlayState|GetPlayState
static PyObject *
py_get_play_state(PyObject *self, PyObject *args)
	{
	CRPlayer *pRPlayer=PyCRPlayer::GetRPlayerWndPtr(self);
	if(pRPlayer==NULL) return NULL;
	GUI_BGN_SAVE;
	long lRet=pRPlayer->GetPlayState();
	GUI_END_SAVE;
	return Py_BuildValue("l",lRet);	
	}
// @pymethod |PyCRPlayer|GetLength|GetLength
static PyObject *
py_get_length(PyObject *self, PyObject *args)
	{
	CRPlayer *pRPlayer=PyCRPlayer::GetRPlayerWndPtr(self);
	if(pRPlayer==NULL) return NULL;
	GUI_BGN_SAVE;
	long lRet=pRPlayer->GetLength();
	GUI_END_SAVE;
	return Py_BuildValue("l",lRet);	
	}

///////////////////////////
// @pymethod |PyCRPlayer|SetClient|Sets a flag used for proper resizing
static PyObject *
py_set_client(PyObject *self, PyObject *args)
	{
	int isclient;
	if(!PyArg_ParseTuple(args, "i", &isclient))
		return NULL;

	CRPlayer *pRPlayerWnd=PyCRPlayer::GetRPlayerWndPtr(self);
	if(pRPlayerWnd==NULL) return NULL;


	GUI_BGN_SAVE;
	pRPlayerWnd->SetClient((isclient!=0));
	GUI_END_SAVE;
	RETURN_NONE;
	}

// @pymethod |PyCRPlayer|CreateRPlayerCtrl|
static PyObject *
py_create_rplayer_ctrl(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	CRPlayer *pRPlayer=PyCRPlayer::GetRPlayerWndPtr(self);
	if(pRPlayer==NULL) return NULL;

	GUI_BGN_SAVE;
	BOOL ret=pRPlayerWnd->CreateRPlayerCtrl();
	GUI_END_SAVE;

	if(!ret) 
		RETURN_ERR("Failed to create RealPlayer control. Check that the control is installed");
	RETURN_NONE;
	}

// @pymethod |PyCRPlayer|DestroyRPlayerCtrl|
static PyObject *
py_destroy_rplayer_ctrl(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	CRPlayer *pRPlayer=PyCRPlayer::GetRPlayerWndPtr(self);
	if(pRPlayer==NULL) return NULL;

	GUI_BGN_SAVE;
	pRPlayerWnd->DestroyRPlayerCtrl();
	GUI_END_SAVE;

	RETURN_NONE;
	}

//////////////////////////////////////////////////////
// @object PyCRPlayer|
static struct PyMethodDef PyCRPlayer_methods[] = {
	{"SetSource",py_set_source,1},
	{"SetControls",py_set_controls,1},

	{"DoPlay",py_do_play,1},
	{"DoStop",py_do_stop,1},
	{"DoPause",py_do_pause,1},
	{"DoPlayPause",py_do_play_pause,1},

  	{"CanPlay",py_can_play,1},
	{"CanStop",py_can_stop,1},
	{"CanPause",py_can_pause,1},

	{"GetPosition",py_get_position,1},
	{"GetPlayState",py_get_play_state,1},
	{"GetLength",py_get_length,1},

    {"SetClient",py_set_client,1},
	{"CreateRPlayerCtrl",py_create_rplayer_ctrl,1},
	{"DestroyRPlayerCtrl",py_destroy_rplayer_ctrl,1},
	{NULL,NULL,1}		
};

ui_type_CObject PyCRPlayer::type("PyCRPlayer", 
								 &PyCWnd::type, 
								 RUNTIME_CLASS(CRPlayer), 
								 sizeof(PyCRPlayer), 
								 PyCRPlayer_methods, 
								 GET_PY_CTOR(PyCRPlayer));
