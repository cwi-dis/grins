#include "stdafx.h"

#include "VViewer.h"


IMPLEMENT_DYNCREATE(CVViewer, CWnd)

BEGIN_MESSAGE_MAP(CVViewer, CWnd)
	//{{AFX_MSG_MAP(CHtmlView)
	ON_WM_SIZE()
	ON_WM_PAINT()
	//}}AFX_MSG_MAP
END_MESSAGE_MAP()

BEGIN_EVENTSINK_MAP(CVViewer, CWnd)
    //{{AFX_EVENTSINK_MAP(CContainerWnd)
	//}}AFX_EVENTSINK_MAP
END_EVENTSINK_MAP()

#define ASSERT_CTRL_EXISTS if(!m_bCtrlCreated){if(!CreateVVCtrl()) return;}
#define ASSERT_CTRL_EXISTS_T if(!m_bCtrlCreated){if(!CreateVVCtrl()) return TRUE;}
#define ASSERT_CTRL_EXISTS_F if(!m_bCtrlCreated){if(!CreateVVCtrl()) return FALSE;}

void CVViewer::OnSize(UINT nType, int cx, int cy)
	{
	CWnd::OnSize(nType, cx, cy);
	FitVVCtrl();
	}

void CVViewer::OnPaint()
	{
	Default();
	}

BOOL CVViewer::Create(LPCTSTR lpszClassName, LPCTSTR lpszWindowName,
						DWORD dwStyle, const RECT& rect, CWnd* pParentWnd,
						UINT nID, CCreateContext* pContext)
	{
	if (!CWnd::Create(lpszClassName, lpszWindowName,
		dwStyle, rect, pParentWnd,  nID, pContext))
		return FALSE;
	return TRUE;
	}

BOOL CVViewer::CreateVVCtrl()
	{
	if(m_bCtrlCreated) return TRUE;
	RECT rectClient;
	GetClientRect(&rectClient);

	// create the control
	if (!m_vvCtrl.Create(NULL, "VViewer",
			WS_CHILD | WS_VISIBLE, rectClient, this, AFX_IDW_PANE_FIRST))
		{
		DestroyWindow();
		return FALSE;
		}
	m_vvCtrl.ShowWindow(SW_SHOW);
	m_bCtrlCreated=true;
	return TRUE;
	}

void CVViewer::DestroyVVCtrl()
	{
	if(!m_bCtrlCreated) return;
	m_vvCtrl.DestroyWindow();
	}

void CVViewer::FitVVCtrl()
	{
	if (!m_bCtrlCreated) return;
	CRect rect;
	GetClientRect(rect);
	::AdjustWindowRectEx(rect,
		m_vvCtrl.GetStyle(), FALSE, WS_EX_CLIENTEDGE);
	if(m_isclient)
		m_vvCtrl.SetWindowPos(NULL, rect.left, rect.top,
			rect.Width(), rect.Height(), SWP_NOACTIVATE | SWP_NOZORDER);
	else
		m_vvCtrl.SetWindowPos(NULL, rect.left+2, rect.top+2,
			rect.Width()-4, rect.Height()-4, SWP_NOACTIVATE | SWP_NOZORDER);
	}

// Control methods (not complete)
void CVViewer::SetSource(LPCTSTR lpszURL)
	{ASSERT_CTRL_EXISTS;m_vvCtrl.SetSrc(lpszURL);}


// static
CVViewer *CVViewer::CreateVViewer(CWnd *pParent,const CRect& rc)
	{
	HBRUSH hbrush=::CreateSolidBrush(RGB(0,0,0));
	HCURSOR hcursor=AfxGetApp()->LoadStandardCursor(IDC_ARROW);
	HICON hicon=0;
	DWORD clstyle=CS_DBLCLKS;
	DWORD style=WS_CHILD | WS_CLIPSIBLINGS | WS_VISIBLE;
	DWORD exstyle = 0 ;
	CString strclass=AfxRegisterWndClass(clstyle,hcursor,hbrush,hicon);
	CVViewer *p=new CVViewer;
	p->Create(strclass,"",style,rc,pParent,0);
	return p;
	}
