#ifndef INC_GRINS_PLAYER
#define INC_GRINS_PLAYER

class GRiNSPlayerApp : public CWinApp
	{
	public:
	virtual BOOL InitInstance();

	//{{AFX_MSG(CNGRiNSPlayerApp)
	afx_msg void OnAppAbout();
	afx_msg void OnCmdExit();
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
	};				  

#endif