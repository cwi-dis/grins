#include "stdafx.h"
#include "resource.h"

#include "MainFrm.h"

#include "grins_main.h"

CMainWindow::CMainWindow()
:	m_is_open(false),
	m_play_state(STOPPED)
	{
	}

BOOL CMainWindow::CreateMainWnd()
	{
	return LoadFrame(IDR_MAINFRAME);
	}

// CMainWindow message map:
BEGIN_MESSAGE_MAP( CMainWindow, CFrameWnd )
	//{{AFX_MSG_MAP( CMainWindow )
	ON_WM_PAINT()
	ON_WM_CLOSE()
	ON_WM_LBUTTONDOWN()
	ON_WM_LBUTTONUP()
	ON_WM_MOUSEMOVE()
	ON_COMMAND(ID_CMD_OPEN, OnCmdOpen)
	ON_UPDATE_COMMAND_UI(ID_CMD_OPEN, OnUpdateCmdOpen)
	ON_COMMAND(ID_CMD_PAUSE, OnCmdPause)
	ON_UPDATE_COMMAND_UI(ID_CMD_PAUSE, OnUpdateCmdPause)
	ON_COMMAND(ID_CMD_PLAY, OnCmdPlay)
	ON_UPDATE_COMMAND_UI(ID_CMD_PLAY, OnUpdateCmdPlay)
	ON_COMMAND(ID_CMD_STOP, OnCmdStop)
	ON_UPDATE_COMMAND_UI(ID_CMD_STOP, OnUpdateCmdStop)
	ON_COMMAND(ID_CMD_CLOSE, OnCmdClose)
	ON_UPDATE_COMMAND_UI(ID_CMD_CLOSE, OnUpdateCmdClose)
	ON_WM_CREATE()
	//}}AFX_MSG_MAP
END_MESSAGE_MAP()


BOOL CMainWindow::PreCreateWindow(CREATESTRUCT& cs)
	{
	if(!CFrameWnd::PreCreateWindow(cs))
		return FALSE;

	cs.lpszClass = AfxRegisterWndClass(CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS, 
		NULL, HBRUSH(COLOR_WINDOW+1), NULL);
	return TRUE;
	}

int CMainWindow::OnCreate(LPCREATESTRUCT lpCreateStruct) 
	{
	if (CFrameWnd ::OnCreate(lpCreateStruct) == -1)
		return -1;

	m_wndCommandBar.m_bShowSharedNewButton = FALSE;
	if(!m_wndCommandBar.Create(this))
		{
		AfxMessageBox(TEXT("CommandBar.Create() failed"));
		return -1;
		}
	if(!m_wndCommandBar.InsertMenuBar(IDR_MAINFRAME))
		{
		AfxMessageBox(TEXT("InsertMenuBar() failed"));
		return -1;
		}

	if(!m_wndCommandBar.LoadToolBar(IDR_MAINFRAME))
		{
		AfxMessageBox(TEXT("LoadToolBar() failed"));
		return -1;
		}

	if(!m_wndCommandBar.AddAdornments())
		{
		AfxMessageBox(TEXT("AddAdornments() failed"));
		return -1;
		}

	m_ToolTipsTable[0] = MakeString(TEXT("Play"));
	m_ToolTipsTable[1] = MakeString(TEXT("Pause"));
	m_ToolTipsTable[2] = MakeString(TEXT("Stop"));
	m_ToolTipsTable[3] = MakeString(TEXT("About"));
	ASSERT(NUM_TOOL_TIPS == 4);
	if(!m_wndCommandBar.PostMessage(TB_SETTOOLTIPS, (WPARAM)(NUM_TOOL_TIPS), (LPARAM)(m_ToolTipsTable)))
		{
		AfxMessageBox(TEXT("SendMessage(TB_SETTOOLTIPS, ...) failed"));
		return -1;    
		}

	m_wndCommandBar.SetBarStyle(m_wndCommandBar.GetBarStyle() |
		CBRS_TOOLTIPS | CBRS_SIZE_FIXED);

	AddAdornments(0);

	return 0;
	}

LPTSTR CMainWindow::MakeString(LPCTSTR psz)
	{
	TCHAR* theString = new TCHAR[lstrlen(psz) + 1];
	lstrcpy(theString, psz);
	return theString;
	}   

void CMainWindow::OnLButtonDown(UINT nFlags, CPoint point) 
	{
	CFrameWnd::OnLButtonDown(nFlags, point);
	}

void CMainWindow::OnLButtonUp(UINT nFlags, CPoint point) 
	{
	CFrameWnd ::OnLButtonUp(nFlags, point);
	}

void CMainWindow::OnMouseMove(UINT nFlags, CPoint point) 
	{
	CFrameWnd ::OnMouseMove(nFlags, point);
	}

void CMainWindow::OnCmdOpen() 
	{
	CString filename;
	if(!DoOpenFileDialog(filename))
		return; // open cancelled
	if(g_pGRiNSMain != NULL)
		{
		if(g_pGRiNSMain->open_file(TEXT("\\My Documents\\Presentations\\slideshow-1.smil")))
			{
			m_is_open = true;
			m_play_state = STOPPED;
			}
		}
	}

void CMainWindow::OnUpdateCmdOpen(CCmdUI* pCmdUI) 
	{
	pCmdUI->Enable(!m_is_open);
	}

void CMainWindow::OnCmdClose() 
	{
	m_is_open = false;
	m_play_state = STOPPED;
	}

void CMainWindow::OnUpdateCmdClose(CCmdUI* pCmdUI) 
	{
	pCmdUI->Enable(m_is_open);
	}

void CMainWindow::OnCmdPlay() 
	{
	m_play_state = PLAYING;
	}

void CMainWindow::OnUpdateCmdPlay(CCmdUI* pCmdUI) 
	{
	pCmdUI->Enable(m_is_open && (m_play_state == STOPPED || m_play_state == PAUSING));
	}

void CMainWindow::OnCmdPause()
	{
	if(m_play_state == PAUSING)
		m_play_state = PLAYING;
	else if(m_play_state == PLAYING)
		m_play_state = PAUSING;
	}

void CMainWindow::OnUpdateCmdPause(CCmdUI* pCmdUI) 
	{
	pCmdUI->Enable(m_is_open && (m_play_state == PLAYING || m_play_state == PAUSING));
	}

void CMainWindow::OnCmdStop() 
	{
	m_play_state = STOPPED;
	}

void CMainWindow::OnUpdateCmdStop(CCmdUI* pCmdUI) 
	{
	pCmdUI->Enable(m_is_open && (m_play_state == PLAYING || m_play_state == PAUSING));
	}

void CMainWindow::OnPaint() 
	{
	CPaintDC dc(this);
	CRect rect;
	GetClientRect(&rect);
	rect.bottom -= MENU_BAR_HEIGHT;
	CString str(TEXT("Oratrix GRiNS Player"));
	dc.DrawText(str, &rect, DT_CENTER | DT_VCENTER);
	}

void CMainWindow::OnClose() 
	{
	CFrameWnd::OnClose();
	}

bool CMainWindow::DoOpenFileDialog(CString& fileName)
	{
	BOOL bOpenFileDialog = TRUE;
	CString strDefExt = TEXT("SMIL Presentation");
	DWORD flags = OFN_HIDEREADONLY | OFN_FILEMUSTEXIST;
	CString strFilter = TEXT("SMIL presentation|*.smil;*.smi;*.grins|");
	strFilter += TEXT("SMIL presentations (*.smil;*.smi)|*.smil;*.smi|");
	strFilter += TEXT("GRiNS Project files (*.grins)|*.grins|");
	strFilter += TEXT("All files (*.*)|*.*||");

	CFileDialog dlg(TRUE, strDefExt, NULL, flags, strFilter, this);

	dlg.m_ofn.lpstrTitle = TEXT("Open presentation");
	dlg.m_ofn.lpstrInitialDir = TEXT("\\My Documents\\Presentations\\");

	if(dlg.DoModal() == IDOK)
		{
		fileName = dlg.GetPathName();
		return true;
		}
	return false;
	}


