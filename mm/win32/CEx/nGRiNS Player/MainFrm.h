#ifndef INC_MAINFRM
#define INC_MAINFRM

#define MENU_BAR_HEIGHT 26
const UINT WM_KICKIDLE = 0x036A;

class CMainWindow : public CFrameWnd
	{
	public:
	CMainWindow();
	BOOL CreateMainWnd();

	private:
	CCeCommandBar m_wndCommandBar;

	bool m_is_open;
	
	enum PlayState {STOPPED, PAUSING, PLAYING};
	PlayState m_play_state;

	enum {NUM_TOOL_TIPS = 4};
	LPTSTR m_ToolTipsTable[NUM_TOOL_TIPS]; 
	LPTSTR MakeString(LPCTSTR psz);
	bool DoOpenFileDialog(CString& fileName);

	// Overrides
	// ClassWizard generated virtual function overrides
	//{{AFX_VIRTUAL(CMainFrame)
	virtual BOOL PreCreateWindow(CREATESTRUCT& cs);
	//}}AFX_VIRTUAL

	public:
	//{{AFX_MSG( CMainWindow )
	afx_msg void OnPaint();
	afx_msg void OnClose();
	afx_msg void OnLButtonDown(UINT nFlags, CPoint point);
	afx_msg void OnLButtonUp(UINT nFlags, CPoint point);
	afx_msg void OnMouseMove(UINT nFlags, CPoint point);
	afx_msg void OnCmdOpen();
	afx_msg void OnUpdateCmdOpen(CCmdUI* pCmdUI);
	afx_msg void OnCmdPause();
	afx_msg void OnUpdateCmdPause(CCmdUI* pCmdUI);
	afx_msg void OnCmdPlay();
	afx_msg void OnUpdateCmdPlay(CCmdUI* pCmdUI);
	afx_msg void OnCmdStop();
	afx_msg void OnUpdateCmdStop(CCmdUI* pCmdUI);
	afx_msg void OnCmdClose();
	afx_msg void OnUpdateCmdClose(CCmdUI* pCmdUI);
	afx_msg int OnCreate(LPCREATESTRUCT lpCreateStruct);
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
	};

#endif // INC_MAINFRM
