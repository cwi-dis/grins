#include "stdafx.h"
#include "resource.h"

#include "GRiNS Player.h"

#include "MainFrm.h"
#include "AboutDlg.h"

#include "grins_main.h"

GRiNSPlayerApp grins_app;

grins::Main *g_pGRiNSMain;

BOOL GRiNSPlayerApp::InitInstance()
	{
	CMainWindow *pMainWnd = new CMainWindow();
	m_pMainWnd = pMainWnd;
	AfxGetThread()->m_pMainWnd = pMainWnd;
	if(!pMainWnd->CreateMainWnd())
		return FALSE;

	m_pMainWnd->ShowWindow(m_nCmdShow);
	m_pMainWnd->UpdateWindow();
	g_pGRiNSMain = new grins::Main(m_lpCmdLine);
	return TRUE;
	}

// GRiNSPlayerApp message map:
BEGIN_MESSAGE_MAP( GRiNSPlayerApp, CWinApp )
	//{{AFX_MSG_MAP( GRiNSPlayerApp)
	ON_COMMAND(ID_APP_ABOUT, OnAppAbout)
	ON_COMMAND(ID_APP_EXIT, OnCmdExit)
	ON_COMMAND(ID_CMD_EXIT, OnCmdExit)
	//}}AFX_MSG_MAP
END_MESSAGE_MAP()

void GRiNSPlayerApp::OnAppAbout()
	{
	CAboutDlg aboutDlg;
	aboutDlg.DoModal();
	}

void GRiNSPlayerApp::OnCmdExit()
	{
	if(g_pGRiNSMain)
		{
		delete g_pGRiNSMain;
		g_pGRiNSMain = NULL;
		}
	if(m_pMainWnd != NULL)
		m_pMainWnd->PostMessage(WM_CLOSE);
	}
