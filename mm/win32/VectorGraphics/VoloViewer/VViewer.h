#ifndef INC_VVIEWER
#define INC_VVIEWER


#if !defined(AFX_AVVIEWX_H__C0085603_AC9A_11D3_8B77_00A0246BC0BD__INCLUDED_)
#include "vviewx.h"
#endif


// the c++/mfc class
class CVViewer: public CWnd
	{
	protected:
	DECLARE_DYNCREATE(CVViewer)
	DECLARE_EVENTSINK_MAP()
	DECLARE_MESSAGE_MAP()

	public:
	CVViewer():m_bCtrlCreated(false),m_isclient(false){}
	virtual ~CVViewer(){}
	virtual BOOL Create(LPCTSTR lpszClassName, LPCTSTR lpszWindowName,
		DWORD dwStyle, const RECT& rect, CWnd* pParentWnd, UINT nID,
		CCreateContext* pContext = NULL);

	// Control creation
	BOOL CreateVVCtrl();
	void DestroyVVCtrl();

	// Operations
	public:
	static CVViewer *CreateVViewer(CWnd *pParent,const CRect& rc);

	/////////////////
	// Control's methods (not complete)
	void SetSource(LPCTSTR lpszURL);
	/////////////////

	void SetClient(bool b){m_isclient=b;}
	void FitVVCtrl();

	//private:
	CVViewX m_vvCtrl;
	bool m_isclient;
	bool m_bCtrlCreated;

	// Generated message map functions
	protected:
	//{{AFX_MSG(CVViewer)
	afx_msg void OnSize(UINT nType, int cx, int cy);
	afx_msg void OnPaint();
	//}}AFX_MSG
	};

#endif
