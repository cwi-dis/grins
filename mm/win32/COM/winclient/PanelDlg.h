// PanelDlg.h : header file
//

#if !defined(AFX_PANELDLG_H__CFBE4EC1_9700_4108_8CF7_950CD64BD730__INCLUDED_)
#define AFX_PANELDLG_H__CFBE4EC1_9700_4108_8CF7_950CD64BD730__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000

/////////////////////////////////////////////////////////////////////////////
// CPanelDlg dialog

class CPanelDlg : public CDialog
{
// Construction
public:
	CPanelDlg(CWnd* pParent = NULL);	// standard constructor

// Dialog Data
	//{{AFX_DATA(CPanelDlg)
	enum { IDD = IDD_WINCLIENT_DIALOG };
		// NOTE: the ClassWizard will add data members here
	//}}AFX_DATA

	// ClassWizard generated virtual function overrides
	//{{AFX_VIRTUAL(CPanelDlg)
	protected:
	virtual void DoDataExchange(CDataExchange* pDX);	// DDX/DDV support
	//}}AFX_VIRTUAL

// Implementation
protected:
	HICON m_hIcon;

	// Generated message map functions
	//{{AFX_MSG(CPanelDlg)
	virtual BOOL OnInitDialog();
	afx_msg void OnSysCommand(UINT nID, LPARAM lParam);
	afx_msg void OnPaint();
	afx_msg HCURSOR OnQueryDragIcon();
	afx_msg void OnButtonBrowse();
	afx_msg void OnButtonPlay();
	afx_msg void OnButtonPause();
	afx_msg void OnButtonStop();
	afx_msg void OnDestroy();
	afx_msg void OnButtonConnect();
	afx_msg void OnButtonDisconnect();
	afx_msg void OnButtonOpen();
	afx_msg void OnButtonClose();
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
};

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ will insert additional declarations immediately before the previous line.

#endif // !defined(AFX_PANELDLG_H__CFBE4EC1_9700_4108_8CF7_950CD64BD730__INCLUDED_)
